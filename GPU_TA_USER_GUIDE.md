# GPU加速非價格TA回測系統用戶指南

## 📖 系統概述

本系統提供GPU加速的非價格數據技術分析回測功能，支持0-300完整參數範圍優化，集成VectorBT專業回測引擎，並提供完整的性能監控和用戶界面。

### 🎯 核心功能

- **GPU加速計算**: 利用CUDA技術實現高性能技術指標計算
- **非價格數據支持**: 集成9個香港政府數據源
- **VectorBT集成**: 專業級回測引擎支持
- **參數優化**: 支持0-300完整參數範圍的GPU並行優化
- **性能監控**: 實時GPU、CPU和內存使用監控
- **CLI工具**: 完整的命令行界面支持

## 🚀 快速開始

### 系統要求

- **Python**: 3.8+
- **CUDA**: 11.0+ (可選，CPU模式完全兼容)
- **GPU**: NVIDIA GPU with CUDA support (可選)
- **內存**: 最低4GB RAM，推薦8GB+
- **磁盤**: 最低10GB可用空間

### 安裝和配置

#### 1. 基礎安裝

```bash
# 克隆項目
git clone <repository-url>
cd CODEX--

# 安裝依賴
pip install -r requirements.txt

# 檢查系統狀態
python gpu_system_status.py
```

#### 2. GPU環境設置

```bash
# 檢查GPU環境
python gpu_system_status.py --json-only

# 如果沒有GPU，系統會自動切換到CPU模式
```

#### 3. 配置遷移（可選）

如果您有舊的配置文件，可以遷移到新的GPU配置：

```bash
# 遷移現有配置
python migrate_gpu_config.py --migrate CODEX--/config/data_sources.yml --backup

# 創建示例配置
python migrate_gpu_config.py --create-sample my_gpu_config.yaml

# 驗證配置文件
python migrate_gpu_config.py --validate my_gpu_config.yaml
```

## 💻 命令行工具使用

### 基本命令結構

```bash
python gpu_ta_cli.py <command> [options]
```

### 主要命令

#### 1. GPU參數優化

```bash
# 基本RSI優化
python gpu_ta_cli.py optimize --symbol 0700.HK --strategy rsi

# 自定義參數範圍
python gpu_ta_cli.py optimize --symbol 0700.HK --strategy rsi --param-range 10-50

# 輸出到指定文件
python gpu_ta_cli.py optimize --symbol 0700.HK --strategy macd --output my_results

# 強制使用CPU
python gpu_ta_cli.py optimize --symbol 0700.HK --strategy bollinger --cpu-only
```

#### 2. VectorBT回測

```bash
# 基本回測
python gpu_ta_cli.py backtest --symbol 0700.HK --strategy rsi

# 多策略回測
python gpu_ta_cli.py backtest --symbol 0700.HK --strategy macd --param-range 12-26 --output macd_backtest

# 詳細輸出
python gpu_ta_cli.py backtest --symbol 0700.HK --strategy sma_crossover --verbose
```

#### 3. 性能基準測試

```bash
# 運行基準測試
python gpu_ta_cli.py benchmark

# 查看詳細性能信息
python gpu_ta_cli.py benchmark --verbose
```

#### 4. 系統健康檢查

```bash
# 完整系統檢查
python gpu_ta_cli.py check

# 快速狀態檢查
python gpu_system_status.py

# 監控模式（30秒刷新）
python gpu_system_status.py --watch

# 自定義刷新間隔
python gpu_system_status.py --watch --interval 60
```

### 參數說明

| 參數 | 說明 | 默認值 | 示例 |
|------|------|--------|------|
| `--symbol` | 股票代碼 | 0700.HK | `--symbol 0941.HK` |
| `--strategy` | 策略類型 | rsi | `--strategy macd` |
| `--param-range` | 參數範圍 | - | `--param-range 10-30` |
| `--output` | 輸出文件前綴 | 時間戳 | `--output my_test` |
| `--cpu-only` | 強制使用CPU | False | `--cpu-only` |
| `--verbose` | 詳細輸出 | False | `--verbose` |

## 📊 支持的策略類型

### 1. RSI均值回歸策略

```bash
python gpu_ta_cli.py optimize --strategy rsi --param-range 10-50
```

**參數範圍**: 週期 1-300

### 2. MACD交叉策略

```bash
python gpu_ta_cli.py optimize --strategy macd --param-range 12-26 50-100
```

**參數範圍**:
- 快線: 1-50
- 慢線: 51-300
- 信號線: 1-20

### 3. 布林帶策略

```bash
python gpu_ta_cli.py optimize --strategy bollinger --param-range 10-50
```

**參數範圍**:
- 週期: 1-300
- 標準差: 1-5

### 4. 雙移動平均策略

```bash
python gpu_ta_cli.py optimize --strategy sma_crossover --param-range 10-30 50-100
```

**參數範圍**:
- 短期均線: 1-100
- 長期均線: 101-300

## 🔧 配置文件詳解

### GPU配置

```yaml
gpu:
  detection:
    auto_detect: true
    fallback_to_cpu: true
    min_compute_capability: 3.5
    min_memory_mb: 2048

  memory:
    max_allocation_ratio: 0.8
    batch_size: 1000
    enable_memory_pool: true

  performance:
    enable_mixed_precision: false
    thread_block_size: 256
```

### 數據源配置

```yaml
data_sources:
  government_data:
    enabled_sources: ["hibor", "monetary_base", "gdp"]

    hibor:
      enabled: true
      priority: 1
      update_frequency: "daily"
```

### VectorBT配置

```yaml
vectorbt:
  settings:
    enable_gpu: true
    use_numba: true
    chunk_size: "auto"
    max_workers: 4

  strategies:
    rsi:
      optimization_range:
        period: [10, 50]
        upper_band: [65, 80]
        lower_band: [20, 35]
```

## 📈 性能監控

### 實時監控

```bash
# 基本狀態顯示
python gpu_system_status.py

# 監控模式
python gpu_system_status.py --watch --interval 30

# 導出JSON格式狀態
python gpu_system_status.py --export status.json
```

### 監控指標

- **GPU狀態**: 利用率、內存使用、溫度
- **內存狀態**: CPU和GPU內存使用情況
- **數據源狀態**: 9個政府數據源的健康狀況
- **VectorBT狀態**: 庫版本和GPU加速可用性
- **系統性能**: CPU使用率、磁盤空間等

## 🔍 故障排除

### 常見問題

#### 1. GPU不可用

**問題**: 顯示"GPU不可用"
**解決方案**:
```bash
# 檢查CUDA安裝
nvidia-smi

# 檢查CuPy安裝
python -c "import cupy; print(cupy.__version__)"

# 使用CPU模式
python gpu_ta_cli.py optimize --cpu-only
```

#### 2. 數據源連接失敗

**問題**: 數據源健康檢查失敗
**解決方案**:
```bash
# 檢查網絡連接
ping api.hkma.gov.hk

# 驗證數據源
python gpu_ta_cli.py check

# 使用Mock數據（開發模式）
export USE_MOCK_DATA=true
```

#### 3. 內存不足

**問題**: GPU或CPU內存不足
**解決方案**:
```bash
# 調整批次大小
python gpu_ta_cli.py optimize --batch-size 500

# 監控內存使用
python gpu_system_status.py --watch

# 使用較小的參數範圍
python gpu_ta_cli.py optimize --param-range 10-20
```

#### 4. VectorBT安裝問題

**問題**: VectorBT導入失敗
**解決方案**:
```bash
# 安裝VectorBT
pip install vectorbt

# 安裝TA-Lib (Windows)
# 下載並安裝從: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

# 安裝TA-Lib (Linux/Mac)
conda install -c conda-forge ta-lib
```

### 日志查看

```bash
# 查看系統日志
tail -f logs/gpu_ta_performance.log

# 查看錯誤日志
grep ERROR logs/gpu_ta_performance.log
```

## 🚀 進階用法

### 1. 批量優化

```bash
#!/bin/bash
# 批量優化多個股票

symbols=("0700.HK" "0941.HK" "1398.HK" "1299.HK")
strategies=("rsi" "macd" "bollinger")

for symbol in "${symbols[@]}"; do
    for strategy in "${strategies[@]}"; do
        echo "Optimizing $symbol with $strategy..."
        python gpu_ta_cli.py optimize --symbol $symbol --strategy $strategy \
            --output "${symbol}_${strategy}_results"
    done
done
```

### 2. 自定義配置

```bash
# 使用自定義配置
python gpu_ta_cli.py optimize --config my_config.yaml

# 驗證配置
python migrate_gpu_config.py --validate my_config.yaml
```

### 3. 結果分析

```python
# 分析優化結果
import json
import pandas as pd

# 讀取結果
with open('results_20251124_143022.json', 'r') as f:
    results = json.load(f)

# 轉換為DataFrame
df = pd.DataFrame(results['strategies'])

# 找到最佳策略
best_strategy = df.loc[df['sharpe_ratio'].idxmax()]
print(f"Best strategy: {best_strategy['parameters']}")
print(f"Sharpe ratio: {best_strategy['sharpe_ratio']:.4f}")
```

## 📚 API參考

### CLI工具

- `gpu_ta_cli.py`: 主要CLI工具
- `gpu_system_status.py`: 系統狀態監控
- `migrate_gpu_config.py`: 配置遷移工具

### 核心模塊

- `src/gpu/`: GPU加速引擎
- `src/adapters/`: 數據源適配器
- `src/vectorization/`: 向量化引擎
- `src/utils/`: 工具模塊

## 🆘 技術支持

### 獲取幫助

```bash
# 查看CLI幫助
python gpu_ta_cli.py --help

# 系統健康檢查
python gpu_ta_cli.py check

# 查看版本信息
python gpu_system_status.py --export version.json
```

### 聯繫支持

- **文檔**: 查看項目README和文檔
- **問題**: 提交GitHub Issues
- **更新**: 定期檢查項目更新

## 📄 版本歷史

### v1.0.0 (2025-11-24)
- ✅ 完整GPU加速支持
- ✅ VectorBT集成
- ✅ CLI工具完整實現
- ✅ 配置管理系統
- ✅ 性能監控功能

---

**注意**: 本系統完全兼容CPU模式，即使沒有GPU也可以正常使用所有功能。GPU加速是可選的性能提升功能。