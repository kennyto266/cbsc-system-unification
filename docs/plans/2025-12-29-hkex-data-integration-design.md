# HKEX 市場數據集成設計

**Date**: 2025-12-29
**Status**: Ready for Implementation
**Phase**: 數據集成 - Phase 1

## 概述

將 HKEX 爬蟲項目的非價格市場數據（漲跌股票數、成交量、成交額等）集成到 CBSC Performance Analysis Tab 的返回歸因模塊中。採用數據庫共享方式，分三個階段逐步實施。

## 技術決策

| 方面 | 選擇 | 理由 |
|------|------|------|
| 數據源 | HKEX 市場數據（優先） | 與返回歸因分析直接相關 |
| 集成方式 | 數據庫共享 | 數據集中、可查詢歷史 |
| 表結構 | 混合方式（原始+指標+觸發器） | 兼顧數據保留和查詢性能 |
| 指標範圍 | 分階段全指標 | 從基礎到進階逐步擴展 |

## 架構設計

### 整體架構

```
┌─────────────────────────────────────────────────────────────┐
│                     HKEX 爬蟲項目                            │
│  crawler.js → database-writer.js → PostgreSQL 數據庫        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  CBSC PostgreSQL 數據庫                     │
│  hkex_raw_data (觸發器) → market_indicators                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   CBSC FastAPI 後端                         │
│  /api/analytics/performance → 查詢指標表                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  PerformanceTab 前端                        │
│  fetchPerformanceAnalytics → 顯示返回歸因圖表                │
└─────────────────────────────────────────────────────────────┘
```

### 數據庫表結構

```sql
-- 原始數據表
CREATE TABLE hkex_raw_data (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    trading_volume INTEGER,
    advanced_stocks INTEGER,
    declined_stocks INTEGER,
    unchanged_stocks INTEGER,
    turnover_hkd BIGINT,
    deals INTEGER,
    morning_close DECIMAL(10,2),
    afternoon_close DECIMAL(10,2),
    change_value DECIMAL(10,2),
    change_percent DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 指標表（Phase 1）
CREATE TABLE market_indicators (
    date DATE PRIMARY KEY REFERENCES hkex_raw_data(date),
    advance_decline_ratio DECIMAL(10,4),
    volume_change_percent DECIMAL(10,4),
    sentiment_score DECIMAL(10,2),
    breadth_momentum DECIMAL(10,4),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 觸發器：自動計算指標
CREATE OR REPLACE FUNCTION calculate_indicators()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO market_indicators (date, advance_decline_ratio, volume_change_percent, sentiment_score, breadth_momentum)
    VALUES (
        NEW.date,
        CASE WHEN NEW.declined_stocks > 0
             THEN NEW.advanced_stocks::DECIMAL / (NEW.declined_stocks + 1)
             ELSE NEW.advanced_stocks::DECIMAL END,
        -- volume_change_percent: 與前一日對比
        0, -- 由存儲過程計算
        -- sentiment_score: 加權綜合
        (CASE WHEN NEW.declined_stocks > 0
              THEN NEW.advanced_stocks::DECIMAL / (NEW.declined_stocks + 1)
              ELSE NEW.advanced_stocks::DECIMAL END * 0.4 +
         0 * 0.3 + -- volume_change
         (NEW.advanced_stocks::DECIMAL / NULLIF(NEW.advanced_stocks + NEW.declined_stocks + NEW.unchanged_stocks, 0)) * 0.3
        ) * 100,
        0 -- breadth_momentum: Phase 2 實現
    )
    ON CONFLICT (date) DO UPDATE SET
        advance_decline_ratio = EXCLUDED.advance_decline_ratio,
        volume_change_percent = EXCLUDED.volume_change_percent,
        sentiment_score = EXCLUDED.sentiment_score,
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_indicators
AFTER INSERT ON hkex_raw_data
FOR EACH ROW
EXECUTE FUNCTION calculate_indicators();
```

## 組件修改範圍

### HKEX 爬蟲側

| 文件 | 類型 | 說明 |
|------|------|------|
| `src/database-writer.js` | 新建 | 連接 CBSC PostgreSQL，寫入數據 |
| `src/crawler.js` | 修改 | 調用 database-writer |
| `.env` | 修改 | 添加數據庫連接字符串 |

### CBSC 後端側

| 文件 | 類型 | 說明 |
|------|------|------|
| `src/api/market_data_endpoints.py` | 新建 | `/api/analytics/performance` 端點 |
| `src/services/market_indicator_service.py` | 新建 | 指標計算邏輯 |
| `src/db/migrations/xxx_hkex_tables.py` | 新建 | 數據庫遷移腳本 |

### 前端側

| 文件 | 狀態 | 說明 |
|------|------|------|
| `performanceAnalyticsSlice.ts` | 已完成 | 已準備接收真實數據，有 mock 降級 |

## 數據流

### 寫入流程

```
HKEX 爬蟲爬取數據
    ↓
解析 CSV 格式
    ↓
連接 CBSC PostgreSQL
    ↓
插入 hkex_raw_data
    ↓
觸發器自動計算
    ↓
更新 market_indicators
```

### 查詢流程

```
前端: dispatch(fetchPerformanceAnalytics({ timeRange: '1m' }))
    ↓
FastAPI: GET /api/analytics/performance?time_range=1m
    ↓
查詢 market_indicators 表（最近 1 個月）
    ↓
計算返回歸因數據
    ↓
返回 JSON 格式
    ↓
前端: 更新 Redux state，重新渲染圖表
```

## Phase 1 指標計算

### 基礎指標公式

```python
# 1. 漲跌比 (Advance/Decline Ratio)
advance_decline_ratio = advanced_stocks / (declined_stocks + 1)

# 2. 成交量變化率
volume_change_percent = (today_volume - yesterday_volume) / yesterday_volume * 100

# 3. 市場情緒分數
sentiment_score = (
    advance_decline_ratio * 0.4 +
    volume_change_percent * 0.3 +
    (advanced_stocks / total_stocks) * 0.3
) * 100

# 4. 廣義動量 (Phase 1 簡化版)
breadth_momentum = 0  # Phase 2 實現
```

### 返回歸因映射

| 經濟指標 | 對應數據 | 權重 |
|----------|----------|------|
| 市場漲跌情緒 | advance_decline_ratio | 40% |
| 成交量活躍度 | volume_change_percent | 30% |
| 市場廣度 | advanced_stocks / total_stocks | 30% |

## API 規範

### GET /api/analytics/performance

**請求**：
```json
{
  "time_range": "1m" | "3m" | "1y",
  "strategies": ["strategy1", "strategy2"] // 可選
}
```

**響應**：
```json
{
  "return_attribution": {
    "total": 5.23,
    "breakdown": [
      {
        "indicator": "市場漲跌情緒",
        "contribution": 2.1,
        "percentage": 40.2
      },
      {
        "indicator": "成交量活躍度",
        "contribution": 1.5,
        "percentage": 28.7
      },
      {
        "indicator": "市場廣度",
        "contribution": 1.6,
        "percentage": 30.6
      }
    ]
  },
  "risk_exposure": { /* mock 數據 */ },
  "correlations": { /* mock 數據 */ },
  "stress_test": [ /* mock 數據 */ ]
}
```

## 錯誤處理

### 數據庫寫入失敗

```javascript
// database-writer.js
async function writeToDatabase(data) {
  try {
    await client.connect();
    await insertData(data);
  } catch (error) {
    // 降級到文件存儲
    fs.appendFileSync('data/write_errors.log', `${Date.now()}: ${error}\n`);
    // 重試邏輯
    for (let i = 0; i < 3; i++) {
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
      try {
        await insertData(data);
        break;
      } catch {}
    }
  }
}
```

### API 降級策略

```python
# market_data_endpoints.py
@router.get("/analytics/performance")
async def get_performance_analytics(time_range: str):
    try:
        data = await fetch_from_database(time_range)
        if not data:
            # 計算原始數據
            data = await calculate_from_raw(time_range)
        if not data:
            # 降級到 mock 數據
            data = get_mock_data()
        return data
    except Exception as e:
        logger.error(f"Error fetching performance data: {e}")
        return get_mock_data()
```

## 測試策略

### 單元測試

| 測試文件 | 測試內容 |
|----------|----------|
| `test_database_writer.py` | 數據庫連接、插入、更新邏輯 |
| `test_indicator_calculation.py` | 指標計算公式正確性 |
| `test_api_endpoint.py` | API 端點響應格式 |

### 集成測試

1. 使用爬蟲歷史 CSV 數據導入測試
2. 驗證完整數據流：爬蟲 → 數據庫 → API → 前端
3. 邊界條件：空數據、異常值、重複日期

### 手動驗證清單

- [ ] 數據庫表創建成功
- [ ] 觸發器正常工作
- [ ] 爬蟲數據成功寫入數據庫
- [ ] API 返回正確格式的數據
- [ ] 前端圖表顯示真實數據
- [ ] 時間範圍切換正常工作

## 實施階段

### Phase 1 - 基礎集成（當前）

✅ 前端 PerformanceTab 已完成
⏳ 數據庫表和觸發器創建
⏳ 爬蟲數據庫寫入模塊
⏳ 後端 API 端點實現
⏳ 集成測試和驗證

### Phase 2 - 進階指標（後續）

⏳ 廣義動量指標實現
⏳ 資金流分析
⏳ 前端圖表交互優化

### Phase 3 - 生產優化（可選）

⏳ WebSocket 實時推送
⏳ Redis 緩存優化
⏳ 性能監控和告警

## 環境配置

### CBSC 數據庫連接

```env
# CBSC backend .env
DATABASE_URL=postgresql://user:password@localhost:5432/cbsc
```

### HKEX 爬蟲配置

```env
# HKEX 爬蟲 .env
CBSC_DATABASE_URL=postgresql://user:password@localhost:5432/cbsc
BACKUP_DATA_DIR=data/
```

## 依賴項

### HKEX 爬蟲新增依賴

```json
{
  "pg": "^8.11.3"
}
```

### CBSC 後端現有依賴

- SQLAlchemy（已有）
- asyncpg（已有）
- FastAPI（已有）

## 成功標準

1. ✅ 數據庫表創建成功，觸發器正常工作
2. ✅ 爬蟲每日數據成功寫入 CBSC 數據庫
3. ✅ API 端點返回正確的返回歸因數據
4. ✅ 前端 PerformanceTab 顯示真實 HKEX 數據
5. ✅ 時間範圍切換（1w/1m/3m/1y）正常工作
6. ✅ Mock 數據降級機制正常運作

## 已知限制

1. Phase 1 只實現基礎指標，進階指標在 Phase 2
2. 數據更新頻率依賴爬蟲執行頻率（目前每日一次）
3. API 暫不支持自定義時間範圍，只支持預設選項
4. 相關性熱力圖和壓力測試仍使用 mock 數據
