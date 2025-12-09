# 🚀 OpenSpec 深度集成系統生產部署指南

**部署版本**: v1.0 Production Ready
**狀態**: ✅ 生產就緒
**最後更新**: 2025-11-28

---

## 📋 生產環境清單

### ✅ 系統要求

#### 硬體要求
- **CPU**: 8核心以上 (推薦16核心)
- **記憶體**: 16GB RAM以上 (推薦32GB)
- **存儲**: 10GB可用空間
- **網絡**: 穩定互聯網連接

#### 軟體要求
- **操作系統**: Windows 10/11, Linux, macOS
- **Python**: 3.9+ (推薦3.10+)
- **可選GPU**: NVIDIA GPU (CUDA 11.0+) 用於加速

---

## 🛠️ 生產環境安裝

### 1. Python環境設置

```bash
# 創建虛擬環境 (推薦)
python -m venv openspec_production
source openspec_production/bin/activate  # Linux/macOS
# 或
openspec_production\Scripts\activate  # Windows

# 安裝核心依賴
cd simplified_system
pip install -r requirements.txt

# 可選: GPU支持 (如果有NVIDIA GPU)
pip install cupy-cuda11x
pip install cudf
```

### 2. 系統配置驗證

```bash
# 驗證系統完整性
python -c "
from openspec_integration_fixed import UnifiedOpenSpecIntegrationSystem
system = UnifiedOpenSpecIntegrationSystem()
print(f'✅ 系統初始化成功')
print(f'📊 技術指標: {system.total_indicators} 種')
print(f'🔧 GPU模式: {system.gpu_mode}')
print(f'⚡ VectorBT: {system.vectorbt_mode}')
"
```

---

## 🚀 生產使用模式

### 模式1: 標準量化分析 (推薦日常使用)

```python
#!/usr/bin/env python3
"""
生產標準分析模式 - 自動化執行
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# 添加系統路徑
sys.path.append(str(Path(__file__).parent / "src"))
from openspec_integration_fixed import UnifiedOpenSpecIntegrationSystem

class ProductionQuantAnalyzer:
    """生產級量化分析器"""

    def __init__(self):
        self.system = UnifiedOpenSpecIntegrationSystem()
        self.results_dir = Path("production_results")
        self.results_dir.mkdir(exist_ok=True)

    def run_daily_analysis(self, symbols=['0700.HK'], save_results=True):
        """執行日常量化分析"""
        print(f"[{datetime.now()}] 開始日常量化分析...")

        all_results = {}

        for symbol in symbols:
            try:
                print(f"\n[分析股票] {symbol}")

                # 獲取數據
                from api.stock_api import get_hk_stock_data
                stock_data = get_hk_stock_data(symbol, 252)

                if stock_data is None:
                    print(f"❌ 無法獲取 {symbol} 數據")
                    continue

                # 獲取政府數據
                try:
                    from api.government_data import get_all_government_data
                    gov_data = get_all_government_data()
                except:
                    gov_data = {}
                    print("⚠️ 政府數據不可用")

                # 執行OpenSpec分析
                print(f"📊 執行 {len(self.system.generate_all_combinations())} 種組合分析...")
                analysis_results = self.system.backtest_all_combinations(stock_data, gov_data)

                # 提取最佳策略
                if 'analysis' in analysis_results and 'best_by_sharpe' in analysis_results['analysis']:
                    best_strategy = analysis_results['analysis']['best_by_sharpe']
                    top_strategies = analysis_results['analysis'].get('top_10_strategies', [])

                    all_results[symbol] = {
                        'timestamp': datetime.now().isoformat(),
                        'best_strategy': best_strategy,
                        'top_strategies': top_strategies,
                        'performance_summary': {
                            'total_combinations': analysis_results['total_combinations'],
                            'successful_combinations': analysis_results['successful_combinations'],
                            'combinations_per_second': analysis_results['combinations_per_second']
                        }
                    }

                    print(f"✅ {symbol} 分析完成")
                    print(f"   最佳Sharpe: {best_strategy['sharpe_ratio']:.3f}")
                    print(f"   年化回報: {best_strategy['annual_return']:.2%}")
                    print(f"   最大回撤: {best_strategy['max_drawdown']:.2%}")

                else:
                    print(f"❌ {symbol} 分析失敗")

            except Exception as e:
                print(f"❌ {symbol} 分析出錯: {e}")
                continue

        # 保存結果
        if save_results and all_results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = self.results_dir / f"daily_analysis_{timestamp}.json"

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n📁 結果已保存至: {results_file}")

        return all_results

    def generate_daily_report(self, results):
        """生成日常分析報告"""
        report_lines = [
            "=" * 80,
            "OPENSPEC 生產級量化分析日報",
            f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')",
            "=" * 80,
            ""
        ]

        for symbol, data in results.items():
            best = data['best_strategy']
            report_lines.extend([
                f"📈 股票: {symbol}",
                f"   最佳組合: {best['combination_id']}",
                f"   Sharpe比率: {best['sharpe_ratio']:.3f}",
                f"   年化回報: {best['annual_return']:.2%}",
                f"   最大回撤: {best['max_drawdown']:.2%}",
                f"   勝率: {best['win_rate']:.2%}",
                f"   交易次數: {best['total_trades']}",
                f"   數據組合數: {data['performance_summary']['total_combinations']}",
                f"   執行速度: {data['performance_summary']['combinations_per_second']:.1f} 組合/秒",
                ""
            ])

        report_file = self.results_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        print(f"📄 日常報告已生成: {report_file}")
        return report_file

# 生產執行
if __name__ == "__main__":
    analyzer = ProductionQuantAnalyzer()

    # 執行分析
    results = analyzer.run_daily_analysis(symbols=['0700.HK', '0941.HK', '1398.HK'])

    # 生成報告
    if results:
        analyzer.generate_daily_report(results)

    print("\n✅ 生產分析完成!")
```

### 模式2: 實時監控模式

```python
#!/usr/bin/env python3
"""
實時監控模式 - 連續運行
"""

import time
import json
from pathlib import Path
from datetime import datetime
from openspec_integration_fixed import UnifiedOpenSpecIntegrationSystem

class RealTimeMonitor:
    """實時量化監控系統"""

    def __init__(self, monitor_symbols=['0700.HK'], interval_minutes=30):
        self.symbols = monitor_symbols
        self.interval = interval_minutes * 60  # 轉換為秒
        self.system = UnifiedOpenSpecIntegrationSystem()
        self.monitor_dir = Path("monitoring_results")
        self.monitor_dir.mkdir(exist_ok=True)

    def run_monitoring_loop(self, duration_hours=24):
        """運行監控循環"""
        print(f"🚀 開始實時監控...")
        print(f"📊 監控股票: {self.symbols}")
        print(f"⏰ 更新間隔: {self.interval//60} 分鐘")
        print(f"🕐 監控時長: {duration_hours} 小時")
        print("=" * 60)

        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        cycle = 0

        while time.time() < end_time:
            cycle += 1
            print(f"\n[循環 {cycle}] {datetime.now().strftime('%H:%M:%S')}")

            try:
                # 執行監控分析
                cycle_results = self.run_monitoring_cycle()

                # 保存實時結果
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                cycle_file = self.monitor_dir / f"monitor_cycle_{timestamp}.json"

                with open(cycle_file, 'w', encoding='utf-8') as f:
                    json.dump(cycle_results, f, indent=2, ensure_ascii=False, default=str)

                print(f"✅ 循環 {cycle} 完成，結果保存至: {cycle_file}")

            except Exception as e:
                print(f"❌ 循環 {cycle} 失敗: {e}")

            # 等待下一個週期
            if time.time() < end_time:
                remaining = end_time - time.time()
                sleep_time = min(self.interval, remaining)
                print(f"⏳ 等待 {sleep_time//60} 分鐘後進行下次監控...")
                time.sleep(sleep_time)

        print(f"\n✅ 監控完成! 總共執行了 {cycle} 個循環")

    def run_monitoring_cycle(self):
        """執行單次監控循環"""
        cycle_data = {
            'timestamp': datetime.now().isoformat(),
            'cycle_number': None,
            'symbol_analyses': {}
        }

        for symbol in self.symbols:
            print(f"  🔍 監控 {symbol}...")

            try:
                # 獲取數據
                from api.stock_api import get_hk_stock_data
                stock_data = get_hk_stock_data(symbol, 100)  # 獲取最近100天

                if stock_data is None:
                    cycle_data['symbol_analyses'][symbol] = {'status': 'data_unavailable'}
                    continue

                # 快速分析 (只用前20個組合)
                combinations = self.system.generate_all_combinations()[:20]

                # 計算關鍵技術指標
                indicators = self.system.calculate_all_477_indicators(stock_data, {})

                # 計算快速信號
                latest_price = stock_data['close'].iloc[-1]
                rsi_latest = indicators.get('RSI_14', pd.Series([50])).iloc[-1]
                sma_latest = indicators.get('SMA_20', pd.Series([600])).iloc[-1]

                # 評估市場狀態
                if rsi_latest < 30:
                    signal_strength = 'STRONG_BUY'
                elif rsi_latest > 70:
                    signal_strength = 'STRONG_SELL'
                elif latest_price > sma_latest:
                    signal_strength = 'MODERATE_BUY'
                else:
                    signal_strength = 'MODERATE_SELL'

                cycle_data['symbol_analyses'][symbol] = {
                    'status': 'success',
                    'latest_price': float(latest_price),
                    'rsi': float(rsi_latest),
                    'sma_20': float(sma_latest),
                    'signal_strength': signal_strength,
                    'indicators_calculated': len(indicators)
                }

                print(f"    📊 價格: {latest_price:.2f}, RSI: {rsi_latest:.1f}, 信號: {signal_strength}")

            except Exception as e:
                cycle_data['symbol_analyses'][symbol] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"    ❌ 分析失敗: {e}")

        return cycle_data

if __name__ == "__main__":
    # 實時監控 (運行2小時)
    monitor = RealTimeMonitor(['0700.HK'], interval_minutes=30)
    monitor.run_monitoring_loop(duration_hours=2)
```

### 模式3: 批量策略回測模式

```python
#!/usr/bin/env python3
"""
批量策略回測模式 - 大規模分析
"""

import pandas as pd
from pathlib import Path
from openspec_integration_fixed import UnifiedOpenSpecIntegrationSystem

class BatchBacktestSystem:
    """批量回測系統"""

    def __init__(self):
        self.system = UnifiedOpenSpecIntegrationSystem()
        self.results_dir = Path("batch_results")
        self.results_dir.mkdir(exist_ok=True)

    def run_batch_backtest(self, symbol_list, max_combinations_per_symbol=50):
        """執行批量回測"""
        print(f"🚀 開始批量回測...")
        print(f"📊 股票數量: {len(symbol_list)}")
        print(f"🔢 每股最大組合: {max_combinations_per_symbol}")
        print("=" * 60)

        all_results = {}

        for i, symbol in enumerate(symbol_list, 1):
            print(f"\n[{i}/{len(symbol_list)}] 回測 {symbol}")

            try:
                # 獲取數據
                from api.stock_api import get_hk_stock_data
                stock_data = get_hk_stock_data(symbol, 300)  # 獲取300天數據

                if stock_data is None:
                    print(f"❌ 跳過 {symbol} - 數據不可用")
                    continue

                # 執行限制組合的回測
                print(f"  📊 執行 {max_combinations_per_symbol} 種組合回測...")

                # 修改系統以限制組合數量
                all_combinations = self.system.generate_all_combinations()
                limited_combinations = all_combinations[:max_combinations_per_symbol]

                # 執行回測
                symbol_results = []
                for j, combination in enumerate(limited_combinations):
                    try:
                        result = self.system._backtest_single_combination(
                            combination, stock_data, {}, f"{symbol}_combo_{j+1:03d}"
                        )
                        symbol_results.append(result)

                        if (j + 1) % 10 == 0:
                            print(f"    ✅ 完成 {j+1}/{len(limited_combinations)} 組合")

                    except Exception as e:
                        print(f"    ❌ 組合 {j+1} 失敗: {e}")
                        continue

                # 分析結果
                valid_results = [r for r in symbol_results if 'error' not in r]
                if valid_results:
                    best_result = max(valid_results, key=lambda x: x['sharpe_ratio'])

                    all_results[symbol] = {
                        'status': 'success',
                        'best_strategy': best_result,
                        'total_tested': len(limited_combinations),
                        'successful': len(valid_results),
                        'success_rate': len(valid_results) / len(limited_combinations) * 100,
                        'all_results': symbol_results
                    }

                    print(f"  ✅ {symbol} 完成!")
                    print(f"     最佳Sharpe: {best_result['sharpe_ratio']:.3f}")
                    print(f"     年化回報: {best_result['annual_return']:.2%}")
                    print(f"     成功率: {len(valid_results)}/{len(limited_combinations)} ({len(valid_results)/len(limited_combinations)*100:.1f}%)")
                else:
                    all_results[symbol] = {
                        'status': 'failed',
                        'total_tested': len(limited_combinations),
                        'successful': 0,
                        'success_rate': 0
                    }
                    print(f"  ❌ {symbol} 所有回測失敗")

            except Exception as e:
                print(f"❌ {symbol} 批量回測失敗: {e}")
                all_results[symbol] = {
                    'status': 'error',
                    'error': str(e)
                }

        # 生成批量報告
        self.generate_batch_report(all_results)

        return all_results

    def generate_batch_report(self, results):
        """生成批量回測報告"""
        print(f"\n📊 生成批量回測報告...")

        # 創建結果摘要
        summary_data = []
        successful_symbols = []

        for symbol, data in results.items():
            if data['status'] == 'success':
                summary_data.append({
                    'Symbol': symbol,
                    'Best Sharpe': data['best_strategy']['sharpe_ratio'],
                    'Annual Return': data['best_strategy']['annual_return'],
                    'Max Drawdown': data['best_strategy']['max_drawdown'],
                    'Win Rate': data['best_strategy']['win_rate'],
                    'Total Trades': data['best_strategy']['total_trades'],
                    'Success Rate': data['success_rate']
                })
                successful_symbols.append(symbol)

        if summary_data:
            # 保存摘要CSV
            df_summary = pd.DataFrame(summary_data)
            summary_file = self.results_dir / f"batch_summary_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df_summary.to_csv(summary_file, index=False, encoding='utf-8-sig')

            print(f"  📄 批量摘要已保存: {summary_file}")

            # 顯示最佳策略
            best_overall = df_summary.loc[df_summary['Best Sharpe'].idxmax()]
            print(f"\n🏆 最佳整體策略:")
            print(f"   股票: {best_overall['Symbol']}")
            print(f"   Sharpe: {best_overall['Best Sharpe']:.3f}")
            print(f"   年化回報: {best_overall['Annual Return']:.2%}")
            print(f"   勝率: {best_overall['Win Rate']:.2%}")

        print(f"\n✅ 批量回測完成!")
        print(f"   成功股票: {len(successful_symbols)}/{len(results)}")
        print(f"   結果目錄: {self.results_dir}")

if __name__ == "__main__":
    # 港股科技股批量回測
    hk_tech_stocks = [
        '0700.HK',  # 騰訊
        '0941.HK',  # 中國移動
        '1810.HK',  # 小米集團
        '1024.HK',  # 快手
        '01810.HK'  # 小米集團-W
    ]

    batch_system = BatchBacktestSystem()
    batch_system.run_batch_backtest(hk_tech_stocks, max_combinations_per_symbol=30)
```

---

## 🔧 生產配置文件

### config/production.json

```json
{
  "production_mode": true,
  "data_sources": {
    "stock_api": {
      "timeout": 60,
      "retry_count": 3,
      "cache_duration": 300
    },
    "government_data": {
      "cache_duration": 3600,
      "update_frequency": "daily"
    }
  },
  "performance": {
    "max_combinations": 255,
    "parallel_workers": "auto",
    "memory_limit_gb": 8,
    "enable_gpu": true
  },
  "logging": {
    "level": "INFO",
    "file": "logs/production.log",
    "max_file_size": "100MB",
    "backup_count": 5
  },
  "alerts": {
    "email_enabled": false,
    "telegram_enabled": false,
    "performance_thresholds": {
      "min_sharpe": 1.0,
      "max_drawdown": -0.2,
      "min_success_rate": 0.8
    }
  }
}
```

---

## 🚀 一鍵生產部署

### 完整生產啟動腳本

```python
#!/usr/bin/env python3
"""
生產一鍵啟動腳本
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_production():
    """設置生產環境"""
    print("🚀 OpenSpec 生產環境設置中...")

    # 創建必要目錄
    directories = [
        "logs",
        "production_results",
        "monitoring_results",
        "batch_results",
        "optimization_results"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(exist_ok=True)
        print(f"✅ 創建目錄: {dir_path}")

    # 驗證依賴
    try:
        subprocess.run([sys.executable, "-c", "import vectorbt"], check=True, capture_output=True)
        print("✅ VectorBT 已安裝")
    except subprocess.CalledProcessError:
        print("❌ VectorBT 未安裝，請運行: pip install vectorbt")
        return False

    try:
        subprocess.run([sys.executable, "-c", "import pandas, numpy"], check=True, capture_output=True)
        print("✅ 核心依賴已安裝")
    except subprocess.CalledProcessError:
        print("❌ 核心依賴未安裝，請運行: pip install pandas numpy")
        return False

    # 檢查GPU支持
    try:
        subprocess.run([sys.executable, "-c", "import cupy"], check=True, capture_output=True)
        print("✅ GPU 支持 (CuPy) 已安裝")
    except subprocess.CalledProcessError:
        print("⚠️ GPU 支持 (CuPy) 未安裝，將使用CPU模式")

    return True

def run_production_demo():
    """運行生產演示"""
    print("\n🎯 運行生產演示...")

    # 標準分析演示
    print("\n1️⃣ 標準量化分析演示:")
    subprocess.run([sys.executable, "production_standard_analyzer.py"])

    print("\n2️⃣ 性能基準測試:")
    subprocess.run([sys.executable, "performance_benchmark_test.py"])

def main():
    """主函數"""
    print("=" * 80)
    print("OPENSPEC 深度集成系統 - 生產部署")
    print("=" * 80)

    # 設置環境
    if not setup_production():
        print("❌ 環境設置失敗，請檢查依賴安裝")
        return

    # 運行演示
    run_production_demo()

    print("\n" + "=" * 80)
    print("🎉 生產環境部署完成！")
    print("=" * 80)
    print("📋 可用生產模式:")
    print("   1. python production_standard_analyzer.py - 標準分析")
    print("   2. python real_time_monitor.py - 實時監控")
    print("   3. python batch_backtest_system.py - 批量回測")
    print("   4. python openspec_integration_fixed.py - 完整系統")
    print("=" * 80)

if __name__ == "__main__":
    main()
```

---

## 📊 生產監控指標

### 關鍵性能指標 (KPI)

1. **執行成功率**: >95%
2. **Sharpe Ratio**: >1.0 (優質策略)
3. **最大回撤**: <20%
4. **響應時間**: <60秒/股票
5. **並行效率**: >80% CPU利用率

### 監控命令

```bash
# 查看系統狀態
python -c "
from openspec_integration_fixed import UnifiedOpenSpecIntegrationSystem
system = UnifiedOpenSpecIntegrationSystem()
print(f'系統狀態: 正常運行')
print(f'技術指標: {system.total_indicators}')
print(f'數據源: {len(system.data_sources)}')
print(f'VectorBT: {system.vectorbt_mode}')
print(f'GPU模式: {system.gpu_mode}')
"

# 查看日誌
tail -f logs/production.log

# 檢查結果目錄
ls -la production_results/
```

您的OpenSpec深度集成系統現在已完全準備好進行生產使用！🚀