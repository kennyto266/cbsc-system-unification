# CBSC 系統集成測試框架

這是一個綜合的系統集成測試框架，用於驗證CBSC量化交易策略管理系統的完整性、性能和可靠性。

## 概述

測試框架包含以下核心組件：

1. **端到端系統集成測試** (`test_end_to_end_system.py`) - 完整的系統功能驗證
2. **API測試套件** (`comprehensive_api_test_suite.py`) - 全面的API端點測試
3. **數據完整性驗證** (`data_flow_integrity_validator.py`) - 數據流完整性檢查
4. **性能基準測試** (`performance_benchmark_suite.py`) - 系統性能基準測試
5. **負載測試框架** (`load_testing_framework.py`) - 並發和負載測試
6. **災難恢復測試** (`disaster_recovery_testing.py`) - 系統恢復能力測試

## 安裝依賴

```bash
pip install -r requirements.txt
```

主要依賴包括：
- `aiohttp` - 異步HTTP客戶端
- `asyncpg` - PostgreSQL異步驅動
- `redis` - Redis客戶端
- `psutil` - 系統監控
- `pandas` - 數據分析
- `numpy` - 數值計算
- `matplotlib` - 圖表生成
- `docker` - 容器管理（災難測試）

## 快速開始

### 運行完整測試套件

```bash
python tests/system_integration_runner.py
```

### 運行特定測試模組

```bash
# 端到端測試
python tests/integration/test_end_to_end_system.py

# API測試
python tests/api/comprehensive_api_test_suite.py

# 數據完整性測試
python tests/integrity/data_flow_integrity_validator.py

# 性能基準測試
python tests/performance/performance_benchmark_suite.py

# 負載測試
python tests/load/load_testing_framework.py

# 災難恢復測試（小心使用）
python tests/disaster/disaster_recovery_testing.py
```

### 命令行選項

```bash
python tests/system_integration_runner.py --help

# 選項說明：
--skip-e2e              # 跳過端到端測試
--skip-api              # 跳過API測試
--skip-integrity        # 跳過數據完整性測試
--skip-performance      # 跳過性能測試
--skip-load             # 跳過負載測試
--run-disaster-tests    # 運行災難恢復測試（默認禁用）
--skip-slow            # 跳過慢速測試
--timeout 120          # 設置測試超時（分鐘）
--environment test     # 指定測試環境
--base-url http://localhost:3003  # 指定服務基礎URL
```

## 測試配置

### 環境變量

創建 `.env.test` 文件：

```env
# 數據庫配置
TEST_DB_HOST=localhost
TEST_DB_PORT=5432
TEST_DB_NAME=cbsc_test
TEST_DB_USER=test_user
TEST_DB_PASSWORD=test_password

# Redis配置
TEST_REDIS_HOST=localhost
TEST_REDIS_PORT=6379
TEST_REDIS_DB=1

# InfluxDB配置（監控）
TEST_INFLUX_HOST=localhost
TEST_INFLUX_PORT=8086
TEST_INFLUX_TOKEN=test_token
TEST_INFLUX_ORG=cbsc
TEST_INFLUX_BUCKET=test_metrics

# 服務配置
TEST_BASE_URL=http://localhost:3003
TEST_API_TIMEOUT=30
TEST_CONCURRENT_REQUESTS=10
```

### 數據庫設置

確保測試數據庫存在：

```sql
CREATE DATABASE cbsc_test;
CREATE USER test_user WITH PASSWORD 'test_password';
GRANT ALL PRIVILEGES ON DATABASE cbsc_test TO test_user;
```

## 測試報告

測試完成後，報告將保存在以下位置：

- **詳細JSON報告**: `test_reports/comprehensive_integration_report_YYYYMMDD_HHMMSS.json`
- **Markdown摘要**: `test_reports/integration_test_summary_YYYYMMDD_HHMMSS.md`
- **日誌文件**: `test_logs/system_integration_YYYYMMDD_HHMMSS.log`

## 各模組詳情

### 1. 端到端系統集成測試

驗證完整的用戶流程和系統交互：

- 用戶認證流程
- 策略創建和管理
- 市場數據處理
- 回測執行
- 實時監控
- 錯誤處理

**輸出示例**：
```
END-TO-END INTEGRATION TEST RESULTS
===================================
Overall Success: ✓
Success Rate: 95.2%
Average Response Time: 0.850s
Total Duration: 180.5s
```

### 2. API測試套件

測試所有API端點的功能和響應：

- 認證端點
- 策略管理API
- 市場數據API
- 投資組合API
- 風險管理API
- 監控端點

**測試覆蓋**：
- 響應時間驗證
- 數據格式檢查
- 錯誤處理測試
- 並發請求處理
- 認證授權驗證

### 3. 數據完整性驗證

確保系統中數據流的完整性和一致性：

- 市場數據完整性
- 策略執行一致性
- 投資組合數據驗證
- 跨系統一致性檢查
- 數據類型驗證
- 業務規則驗證

**檢查類型**：
- 校驗和驗證
- 一致性檢查
- 引用完整性
- 時間完整性
- 範圍驗證
- 完整性檢查

### 4. 性能基準測試

測量和監控系統性能指標：

- API響應時間
- 數據庫查詢性能
- 算法執行效率
- 系統資源使用
- 吞吐量測量
- 可擴展性測試

**性能指標**：
- 平均響應時間
- P95/P99響應時間
- 每秒請求數（RPS）
- CPU和內存使用率
- 數據庫連接池效率

### 5. 負載測試框架

模擬真實用戶負載並測試系統承受能力：

- 恒定負載測試
- 漸進負載測試
- 壓力測試
- 尖峰測試
- 耐久性測試
- 並發測試

**負載模式**：
- 恒定負載
- 漸進增加
- 正弦波變化
- 隨機爆發
- 真實用戶行為

### 6. 災難恢復測試

測試系統在故障情況下的恢復能力：

- 數據庫故障恢復
- 緩存故障處理
- 網絡分區恢復
- 服務器崩潰恢復
- 數據損壞恢復
- 業務連續性驗證

**⚠️ 安全注意**：
災難恢復測試會模擬真實的系統故障，請謹慎使用並確保在測試環境中運行。

## 最佳實踐

### 測試執行

1. **定期執行**：在CI/CD流水線中定期運行
2. **測試環境隔離**：使用專門的測試環境
3. **數據準備**：確保測試數據的一致性
4. **資源監控**：監控測試過程中的系統資源

### 結果分析

1. **關注失敗測試**：優先解決關鍵問題
2. **性能趨勢**：跟蹤性能變化趨勢
3. **基線比較**：與歷史基線進行比較
4. **持續改進**：根據測試結果優化系統

### 報告使用

1. **整合監控**：將測試結果整合到監控系統
2. **團隊協作**：與開發團隊共享測試結果
3. **趨勢分析**：長期跟蹤測試趨勢
4. **決策支持**：為系統優化提供數據支持

## 故障排除

### 常見問題

1. **數據庫連接失敗**
   ```
   檢查數據庫服務狀態
   驗證連接參數
   確認網絡連通性
   ```

2. **Redis連接錯誤**
   ```
   檢查Redis服務
   驗證端口配置
   確認認證設置
   ```

3. **API超時**
   ```
   檢查服務狀態
   調整超時設置
   驗證網絡連接
   ```

4. **內存不足**
   ```
   監控內存使用
   調整並發參數
   優化測試配置
   ```

### 調試技巧

1. **啟用詳細日誌**
   ```python
   logging.getLogger().setLevel(logging.DEBUG)
   ```

2. **運行單個測試**
   ```bash
   python -m pytest tests/test_specific.py -v
   ```

3. **檢查系統資源**
   ```bash
   htop  # CPU和內存
   iotop # I/O使用
   netstat -an | grep :3003  # 網絡連接
   ```

## 貢獻指南

### 添加新測試

1. 創建測試文件
2. 繼承適當的基類
3. 實現測試方法
4. 添加配置選項
5. 更新文檔

### 代碼規範

```python
# 使用類型提示
async def test_function(param: str) -> bool:
    """測試函數文檔"""
    # 實現
    pass

# 異常處理
try:
    # 測試邏輯
    pass
except SpecificException as e:
    logger.error(f"測試失敗: {str(e)}")
    raise
```

## 聯繫和支持

如有問題或建議，請通過以下方式聯繫：

- 項目倉庫：[GitHub Repository]
- 技術支持：[Support Email]
- 文檔：[Documentation Link]

---

**注意**：本測試框架僅用於測試環境，請勿在生產環境中運行災難恢復測試。