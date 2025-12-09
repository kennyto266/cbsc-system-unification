# 企業級測試框架
# Enterprise Testing Framework

為香港量化交易微服務系統提供全面的測試保障，確保代碼質量、性能和安全性。

## 📊 測試覆蓋範圍

### 🎯 測試層次

| 測試類型 | 覆蓋範圍 | 標記 | 執行頻率 |
|---------|---------|------|----------|
| **單元測試** | 獨立函數/類 | `@pytest.mark.unit` | 每次提交 |
| **集成測試** | 模塊間交互 | `@pytest.mark.integration` | 每次PR |
| **端到端測試** | 完整業務流程 | `@pytest.mark.e2e` | 每日 |
| **性能測試** | 負載/壓力測試 | `@pytest.mark.performance` | 每周 |
| **安全測試** | 安全漏洞檢查 | `@pytest.mark.security` | 每日 |

### 🧪 核心測試領域

#### 1. 數據質量測試
- **HIBOR數據驗證** (`tests/unit/simplified_system/test_hibor_data.py`)
- **股票數據完整性** (`tests/unit/simplified_system/test_stock_data_quality.py`)
- **異常數據處理** (`tests/unit/shared/test_data_validation.py`)

#### 2. Sharpe比率計算測試
- **標準化計算器** (`tests/unit/shared/test_sharpe_calculator.py`)
- **邊界條件測試** (`tests/unit/shared/test_sharpe_edge_cases.py`)
- **精度驗證** (`tests/performance/test_sharpe_performance.py`)

#### 3. 回測引擎測試
- **VectorBT集成** (`tests/unit/simplified_system/test_vectorbt_engine.py`)
- **策略邏輯測試** (`tests/integration/test_strategy_logic.py`)
- **風險指標測試** (`tests/integration/test_risk_metrics.py`)

#### 4. 技術指標測試
- **477種指標計算** (`tests/unit/simplified_system/test_core_indicators.py`)
- **性能基準測試** (`tests/performance/test_indicators_performance.py`)
- **GPU加速測試** (`tests/performance/test_gpu_acceleration.py`)

## 🚀 快速開始

### 安裝測試依賴

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 或使用Makefile
make install-dev
```

### 運行測試

```bash
# 運行所有測試
pytest

# 運行特定類型測試
pytest -m unit          # 單元測試
pytest -m integration    # 集成測試
pytest -m performance    # 性能測試
pytest -m security       # 安全測試

# 並行執行測試
pytest -n auto

# 生成覆蓋率報告
pytest --cov=simplified_system --cov=backend --cov-report=html
```

### 使用Makefile

```bash
# 運行所有測試
make test-all

# 快速測試（不包括性能和安全）
make test-fast

# 代碼質量檢查
make quality

# 完整CI流水線
make ci
```

## 📁 目錄結構

```
tests/
├── __init__.py              # 測試框架初始化
├── conftest.py             # 全局fixtures和配置
├── factories/              # 測試數據工廠
│   ├── stock_data_factory.py
│   └── indicators_factory.py
├── fixtures/               # 測試數據fixtures
├── unit/                   # 單元測試
│   ├── simplified_system/  # Simplified System測試
│   │   ├── test_stock_api.py
│   │   ├── test_core_indicators.py
│   │   └── test_vectorbt_engine.py
│   ├── backend/            # 後端服務測試
│   │   └── test_data_service.py
│   └── shared/             # 共享組件測試
├── integration/            # 集成測試
│   ├── api_integration.py
│   ├── database/
│   │   └── test_database_integration.py
│   └── external_services/
├── performance/            # 性能測試
│   ├── test_indicators_performance.py
│   ├── test_sharpe_performance.py
│   └── load/
├── security/               # 安全測試
│   ├── test_api_security.py
│   ├── test_data_privacy.py
│   └── auth/
├── e2e/                    # 端到端測試
└── utils/                  # 測試工具
    ├── performance_profiler.py
    └── data_validator.py
```

## 🏷️ 測試標記說明

### 標準標記
- `@pytest.mark.unit` - 單元測試
- `@pytest.mark.integration` - 集成測試
- `@pytest.mark.e2e` - 端到端測試
- `@pytest.mark.performance` - 性能測試
- `@pytest.mark.security` - 安全測試

### 專門標記
- `@pytest.mark.slow` - 慢速測試（需要較長時間）
- `@pytest.mark.gpu` - GPU相關測試
- `@pytest.mark.sharpe` - Sharpe比率計算測試
- `@pytest.mark.vectorbt` - VectorBT專用測試
- `@pytest.mark.hibor` - HIBOR數據測試
- `@pytest.mark.external` - 外部API依賴測試

### 運行標記測試

```bash
# 只運行單元測試
pytest -m unit

# 排除慢速測試
pytest -m "not slow"

# 組合標記
pytest -m "unit and not slow"
pytest -m "performance or gpu"
```

## 🔧 測試配置

### Pytest配置 (pyproject.toml)

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "--strict-markers",
    "--cov=.",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=85"
]
testpaths = ["tests"]
markers = [
    "unit: 單元測試",
    "integration: 集成測試",
    "performance: 性能測試",
    "security: 安全測試"
]
```

### 覆蓋率配置

```bash
# 生成覆蓋率報告
pytest --cov=simplified_system --cov=backend --cov-report=html

# 查看報告
open htmlcov/index.html
```

## 📊 性能測試

### 基準測試

```bash
# 運行性能基準測試
pytest tests/performance/ --benchmark-only

# 生成性能報告
pytest tests/performance/ --benchmark-only --benchmark-html=report.html
```

### 性能回歸檢測

```bash
# 分析性能變化
python .github/scripts/analyze_performance.py \
    --current benchmark-results.json \
    --threshold 10
```

## 🔒 安全測試

### 運行安全檢查

```bash
# 運行安全測試
pytest tests/security/

# Bandit安全掃描
bandit -r simplified_system/src backend/

# Safety依賴安全檢查
safety check
```

### 安全測試覆蓋

- **SQL注入防護** (`tests/security/test_sql_injection.py`)
- **XSS防護** (`tests/security/test_xss_protection.py`)
- **認證繞過** (`tests/security/test_auth_bypass.py`)
- **數據隱私** (`tests/security/test_data_privacy.py`)

## 🐳 CI/CD集成

### GitHub Actions

- **觸發條件**: Push到main/develop, Pull Request, 每日定時
- **測試矩陣**: 多Python版本 (3.9-3.12) + 多操作系統
- **並行執行**: 單元測試、集成測試、性能測試、安全測試
- **覆蓋率報告**: 自動上傳到Codecov

### 本地CI測試

```bash
# 模擬CI流水線
make ci

# 預提交檢查
make pre-commit
```

## 📈 測試數據管理

### 數據工廠

使用Factory Boy模式生成測試數據：

```python
from tests.factories.stock_data_factory import create_test_stock_data

# 生成測試數據
stock_data = create_test_stock_data("0700.HK", 100)
hibor_data = create_test_hibor_data(365)
```

### 測試數據集

- **股票數據**: 真實港股數據 + 模擬數據
- **HIBOR數據**: 香港銀行同業拆息數據
- **技術指標**: 477種技術指標測試用例
- **回測結果**: VectorBT回測樣本數據

## 🔍 調試和故障排除

### 常見問題

1. **測試超時**
   ```bash
   # 增加超時時間
   pytest --timeout=600
   ```

2. **內存不足**
   ```bash
   # 限制並行測試
   pytest -n 2
   ```

3. **外部依賴失敗**
   ```bash
   # 跳過外部依賴測試
   pytest -m "not external"
   ```

### 調試工具

```bash
# 運行單個測試並輸出詳細信息
pytest tests/unit/simplified_system/test_stock_api.py::test_get_stock_data_success -v -s

# 運行失敗的測試
pytest --lf

# 停在第一個失敗
pytest -x
```

## 📋 測試清單

### 提交前檢查

- [ ] 所有單元測試通過
- [ ] 代碼格式符合標準 (Black + isort)
- [ ] 類型檢查通過 (MyPy)
- [ ] 安全掃描通過 (Bandit)
- [ ] 測試覆蓋率 > 85%

### PR合併前檢查

- [ ] 所有集成測試通過
- [ ] 性能回歸測試通過
- [ ] 安全測試通過
- [ ] 文檔更新完整

## 📚 參考資源

- [Pytest文檔](https://docs.pytest.org/)
- [Coverage.py文檔](https://coverage.readthedocs.io/)
- [Bandit安全測試](https://bandit.readthedocs.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [性能測試最佳實踐](https://pytest-benchmark.readthedocs.io/)

## 🤝 貢獻指南

### 添加新測試

1. **確定測試類型** (單元/集成/性能/安全)
2. **使用合適的標記**
3. **編寫清晰的測試文檔**
4. **添加必要的fixtures**
5. **更新測試覆蓋率**

### 測試命名規範

```python
class TestStockAPI:
    def test_get_stock_data_success(self):
        """測試成功獲取股票數據"""
        pass

    def test_get_stock_data_with_invalid_symbol(self):
        """測試無效股票代碼處理"""
        pass
```

---

**測試框架版本**: 1.0.0
**最後更新**: 2025-11-28
**維護者**: Enterprise Testing Team