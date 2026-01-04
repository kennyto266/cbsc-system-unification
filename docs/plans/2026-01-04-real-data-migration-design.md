# 真實數據遷移計劃設計

**日期**: 2026-01-04
**狀態**: 已批准
**優先級**: 高

## 概述

將 CBSC 量化交易策略管理系統從模擬數據遷移到真實市場數據（Yahoo Finance），採用分階段遷移策略和嚴格錯誤處理模式。

## 設計決策

### 數據源選擇
- **主要數據源**: Yahoo Finance (yfinance)
- **理由**: 免費、易於使用、支持港股和美股、已存在適配器基礎設施

### 實施策略
- **分階段遷移**:
  1. 階段 1: 回測系統遷移
  2. 階段 2: Dashboard 統計數據遷移
  3. 階段 3: 其他模組遷移

### 錯誤處理模式
- **嚴格模式（生產級）**:
  - 數據獲取失敗時返回明確錯誤，不降級到 mock data
  - 實施完整的錯誤處理和日誌記錄
  - 對數據質量進行驗證（缺失值、異常值檢測）

## 架構設計

### 階段 1: 回測系統遷移

**目標文件**: `backend/api/backtest.py`

**核心修改**:

```python
async def run_real_backtest(
    symbol: str,
    strategy: Dict[str, Any],
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """使用真實市場數據運行回測"""

    # 1. 使用 YahooFinanceAdapter 獲取歷史數據
    adapter = YahooFinanceAdapter(config)
    historical_data = await adapter.get_historical_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )

    # 2. 數據驗證
    if not historical_data or len(historical_data) == 0:
        raise ValueError(f"無法獲取 {symbol} 的歷史數據")

    # 3. 應用策略邏輯到真實數據
    # 4. 計算回測指標（收益率、夏普比率等）
```

**錯誤處理策略（嚴格模式）**:
- Yahoo Finance API 超時 → 返回 504 Gateway Timeout
- 數據缺失 → 返回 422 Unprocessable Entity，明確說明缺失範圍
- 無效股票代碼 → 返回 404 Not Found

### 配置管理

**新建文件**: `backend/data_config.py`

```python
from pydantic import BaseSettings

class DataSourceConfig(BaseSettings):
    """數據源配置"""

    # Yahoo Finance 配置
    yahoo_finance_enabled: bool = True
    yahoo_finance_timeout: int = 30  # 秒
    yahoo_finance_retry_attempts: int = 3
    yahoo_finance_retry_delay: int = 1  # 秒

    # 嚴格模式配置
    strict_mode: bool = True  # 不降級到 mock data
    data_validation_enabled: bool = True

    # 緩存配置
    enable_cache: bool = True
    cache_ttl: int = 300  # 5 分鐘

    class Config:
        env_file = ".env"
```

### 數據驗證層

**新建文件**: `backend/services/data_validator.py`

```python
def validate_historical_data(df: pd.DataFrame) -> ValidationResult:
    """驗證歷史數據質量"""

    issues = []

    # 檢查缺失值
    if df.isnull().any().any():
        missing_cols = df.columns[df.isnull().any()].tolist()
        issues.append(f"缺失值在列: {missing_cols}")

    # 檢查價格異常值（負數、零）
    if (df['close'] <= 0).any():
        issues.append("價格數據包含非正數")

    # 檢查時間序列連續性
    date_gaps = detect_date_gaps(df['date'])
    if date_gaps:
        issues.append(f"日期間隙: {date_gaps}")

    return ValidationResult(
        is_valid=len(issues) == 0,
        issues=issues
    )
```

### API 端點修改

**修改文件**: `backend/api/backtest.py`

```python
@app.post("/api/backtest/run")
async def run_backtest_endpoint(request: BacktestRequest):
    """運行回測 - 使用真實數據"""

    try:
        # 使用真實數據回測
        result = await run_real_backtest(
            symbol=request.symbol,
            strategy=request.strategy,
            start_date=request.start_date,
            end_date=request.end_date
        )

        return {
            "success": True,
            "data": result,
            "data_source": "yahoo_finance",  # 標明數據源
            "timestamp": datetime.utcnow().isoformat()
        }

    except YahooFinanceError as e:
        # Yahoo Finance 特定錯誤
        raise HTTPException(
            status_code=503,
            detail=f"Yahoo Finance 數據獲取失敗: {str(e)}"
        )
    except DataValidationError as e:
        # 數據驗證失敗
        raise HTTPException(
            status_code=422,
            detail=f"數據質量檢查失敗: {str(e)}"
        )
```

### 前端集成

**修改文件**: `frontend/src/pages/StrategyBacktest.tsx`

```typescript
// 處理嚴格模式錯誤
if (response.data_source === 'yahoo_finance') {
  // 顯示數據源標識
  showNotification('使用 Yahoo Finance 真實數據', 'info');
}

// 處理 503 錯誤
if (error.response?.status === 503) {
  showError('無法連接 Yahoo Finance，請稍後再試');
}
```

## 測試策略

### 1. 單元測試
- 測試 `YahooFinanceAdapter` 連接和數據獲取
- 測試 `DataValidator` 各種驗證場景
- Mock Yahoo Finance API 響應進行離線測試

### 2. 集成測試
- 測試完整回測流程：API → Adapter → 驗證 → 計算
- 測試錯誤場景：超時、空數據、無效股票代碼

### 3. 真實數據驗證
- 對比真實數據回測結果 vs 舊 mock 數據結果
- 驗證常見股票（0700.HK, AAPL）能正確獲取

## 實施步驟

### 準備階段
1. 創建功能分支：`git checkout -b feature/real-data-migration`
2. 安裝依賴：`pip install yfinance`（已存在）
3. 備份現有 mock 實現

### 開發階段
1. 實施階段 1：回測系統遷移
2. 編寫測試
3. 本地驗證

### 測試階段
1. 運行測試套件
2. 手動驗證真實股票代碼
3. 性能測試

### 部署階段
1. 代碼審查
2. 合併到主分支
3. 監控生產環境

## 後續階段規劃

### 階段 2: Dashboard 統計數據遷移
- 更新 Dashboard API 端點使用真實市場數據
- 實時股票價格、市場指數、投資組合表現
- 實施緩存機制避免頻繁調用 Yahoo Finance API

### 階段 3: 其他模組遷移
- 策略執行引擎
- 實時監控系統
- 風險管理模組

## 依賴項

### 現有基礎設施
- `src/data_adapters/yahoo_finance_adapter.py` - Yahoo Finance 數據適配器
- `src/data_adapters/base_adapter.py` - 基礎適配器接口

### 需要安裝
- `yfinance` - Yahoo Finance API 客戶端（已在 requirements.txt）

## 風險和緩解措施

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| Yahoo Finance API 不穩定 | 高 | 實施重試機制、超時控制、緩存策略 |
| 數據質量問題 | 中 | 嚴格的數據驗證、異常值檢測 |
| API 限制 | 中 | 緩存機制、請求速率控制 |
| 股票代碼變更 | 低 | 定期更新股票代碼映射表 |

## 驗收標準

- [ ] 回測 API 使用真實 Yahoo Finance 數據
- [ ] 錯誤處理符合嚴格模式規範
- [ ] 數據驗證通過所有測試場景
- [ ] 前端正確顯示數據源和錯誤信息
- [ ] 測試覆蓋率 >= 80%
- [ ] 文檔更新完成

## 相關文檔

- Yahoo Finance Adapter: `src/data_adapters/yahoo_finance_adapter.py`
- Base Adapter: `src/data_adapters/base_adapter.py`
- 當前 Mock 實現: `backend/api/backtest.py` (第 111-149 行)
