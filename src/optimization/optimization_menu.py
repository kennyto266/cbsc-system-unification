#!/usr / bin / env python3
"""
Phase 4 參數優化菜單系統
Parameter Optimization Menu System for Phase 4

為互動式量化交易平台提供完整的參數優化界面
Complete parameter optimization interface for interactive quantitative trading platform
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List

from parameter_optimizer import (
OptimizationConfig,
ParameterOptimizer,
compare_all_strategies,
quick_optimize,
)

try:
from tabulate import tabulate

TABULATE_AVAILABLE = True
except ImportError:    TABULATE_AVAILABLE = False

try:
from colorama import Back, Fore, Style, init

init()
COLOR_AVAILABLE = True
except ImportError:    COLOR_AVAILABLE = False

class OptimizationMenu:
"""參數優化菜單"""

def __init__self:    self.optimizer = None
self.last_result = None

def show_menuself:
"""顯示主菜單"""
while True:
self._print_header()
self._print_menu_options()

choice = input("\n請選擇操作 1 - 9: ").strip()

try:    if choice == "1":
self._quick_optimization()
elif choice == "2":
self._custom_optimization()
elif choice == "3":
self._multi_strategy_comparison()
elif choice == "4":
self._load_previous_results()
elif choice == "5":
self._batch_optimization()
elif choice == "6":
self._advanced_settings()
elif choice == "7":
self._view_optimization_history()
elif choice == "8":
self._export_results()
elif choice == "9" or choice.lower() == "q":
print"\n👋 感謝使用參數優化系統！"
break
else:
print"\n❌ 無效選擇，請重試。"
input"按Enter繼續..."

except KeyboardInterrupt:
print"\n\n👋 操作已取消，返回主菜單。"
continue
except Exception as e:
print(f"\n❌ 發生錯誤: {stre}")
input"按Enter繼續..."

def _print_headerself:
"""打印標題"""
os.system"cls" if os.name == "nt" else "clear"
print"=" * 80
print"🎯 Phase 4 參數優化集成系統"
print"=" * 80

def _print_menu_optionsself:
"""打印菜單選項"""
options = [
"1", "⚡ 快速優化", "使用默認參數進行快速參數優化",
"2", "🔧 自定義優化", "設置自定義參數進行優化",
"3", "📊 多策略比較", "比較多個策略的優化結果",
"4", "📂 載入歷史結果", "查看之前的優化結果",
"5", "🚀 批量優化", "對多個股票進行批量優化",
"6", "⚙️ 高級設置", "配置優化參數和系統設置",
"7", "📈 優化歷史", "查看優化歷史記錄",
"8", "💾 導出結果", "導出優化結果到文件",
"9", "🚪 退出程序", "返回主界面",
]

print"\n📋 請選擇操作："
for code, title, desc in options:
if COLOR_AVAILABLE:
print(
f"{Fore.GREEN}{code}{Style.RESET_ALL}. {Fore.YELLOW}{title}{Style.RESET_ALL} - {desc}"
)
else:
printf"{code}. {title} - {desc}"

def _quick_optimizationself:
"""快速優化"""
self._print_header()
print"⚡ 快速參數優化"
print"-" * 50

symbol = input("請輸入股票代碼 默認: 0700.HK: ").strip() or "0700.HK"

strategies = [
"RSI_MEAN_REVERSION",
"MACD_CROSSOVER",
"BOLLINGER_BANDS",
"DUAL_MOVING_AVERAGE",
"MOMENTUM_BREAKOUT",
"VOLATILITY_BREAKOUT",
]

printf"\n可用策略:"
for i, strategy in enumeratestrategies, 1:
printf"{i}. {strategy}"

try:    strategy_choice = int(
input(f"請選擇策略 (1-{lenstrategies}, 默認: 1): ").strip() or "1"
)
if 1 <= strategy_choice <= lenstrategies:    strategy = strategies[strategy_choice - 1]
else:
print"無效選擇，使用默認策略"
strategy = strategies[0]
except ValueError:
print"無效輸入，使用默認策略"
strategy = strategies[0]

try:    max_combinations = int(
input("最大參數組合數 默認: 500: ").strip() or "500"
)
except ValueError:    max_combinations = 500

printf"\n🚀 開始快速優化..."
printf"股票: {symbol}"
printf"策略: {strategy}"
printf"最大組合數: {max_combinations}"
print"-" * 50

try:

time.time()
result = quick_optimizesymbol, strategy, max_combinations
self.last_result = result

self.optimizer = ParameterOptimizer()
self.optimizer.display_resultsresult, detailed = True

self._show_result_optionsresult

except Exception as e:
print(f"❌ 優化失敗: {stre}")

input"\n按Enter返回主菜單..."

def _custom_optimizationself:
"""自定義優化"""
self._print_header()
print"🔧 自定義參數優化"
print"-" * 50

symbol = input("請輸入股票代碼 默認: 0700.HK: ").strip() or "0700.HK"
duration = self._get_int_input("數據天數 默認: 252: ", 252)

strategies = [
"RSI_MEAN_REVERSION",
"MACD_CROSSOVER",
"BOLLINGER_BANDS",
"DUAL_MOVING_AVERAGE",
"MOMENTUM_BREAKOUT",
"VOLATILITY_BREAKOUT",
]

printf"\n可用策略:"
for i, strategy in enumeratestrategies, 1:
printf"{i}. {strategy}"

try:    strategy_choice = int(input(f"請選擇策略 (1-{len(strategies)}): ").strip())
if 1 <= strategy_choice <= lenstrategies:    strategy = strategies[strategy_choice - 1]
else:
raise ValueError"Invalid choice"
except ValueError:
print"無效選擇，使用默認策略"
strategy = strategies[0]

# 獲取自定義參數範圍
param_ranges = self._get_custom_parameter_rangesstrategy

optimization_metric = self._get_optimization_metric()
max_combinations = self._get_int_input("最大參數組合數 默認: 1000: ", 1000)

use_gpu = input("使用GPU加速? y / N, 默認: N: ").strip().lower() == "y"

config = OptimizationConfig(
symbol = symbol,
duration = duration,
strategy = strategy,
optimization_metric = optimization_metric,
max_combinations = max_combinations,
use_gpu = use_gpu,
show_progress = True,
save_intermediate = True,
)

printf"\n🔧 配置摘要:"
printf"股票: {config.symbol}"
printf"策略: {config.strategy}"
printf"優化目標: {config.optimization_metric}"
printf"最大組合: {config.max_combinations}"
printf"GPU加速: {'是' if config.use_gpu else '否'}"
print"-" * 50

confirm = input("\n確認開始優化? Y / n: ").strip().lower()
if confirm == "n":
print"操作已取消"
return

try:

self.optimizer = ParameterOptimizerconfig
start_time = time.time()

printf"\n🚀 開始自定義優化..."
result = self.optimizer.run_optimizationparam_ranges = param_ranges

self.last_result = result
time.time() - start_time

self.optimizer.display_resultsresult, detailed = True

self._show_result_optionsresult

except Exception as e:
print(f"❌ 優化失敗: {stre}")

input"\n按Enter返回主菜單..."

def _multi_strategy_comparisonself:
"""多策略比較"""
self._print_header()
print"📊 多策略比較"
print"-" * 50

symbol = input("請輸入股票代碼 默認: 0700.HK: ").strip() or "0700.HK"

# 選擇要比較的策略
all_strategies = [
"RSI_MEAN_REVERSION",
"MACD_CROSSOVER",
"BOLLINGER_BANDS",
"DUAL_MOVING_AVERAGE",
"MOMENTUM_BREAKOUT",
"VOLATILITY_BREAKOUT",
]

print(f"\n可用策略 選擇要比較的策略:")
for i, strategy in enumerateall_strategies, 1:
printf"{i}. {strategy}"

strategy_input = input(
"請輸入策略編號，用逗號分隔 例如: 1,3,5, 默認: 全部: "
).strip()

if strategy_input:
try:    selected_indices = [
int(x.strip()) - 1 for x in strategy_input.split","
]
strategies = [
all_strategies[i]
for i in selected_indices
if 0 <= i < lenall_strategies
]
except ValueError:
print"無效輸入，使用所有策略"
strategies = all_strategies
else:    strategies = all_strategies

printf"\n📊 將比較以下策略:"
for strategy in strategies:
printf" • {strategy}"

max_combinations = self._get_int_input(
"每個策略的最大組合數 默認: 300: ", 300
)
use_gpu = input("使用GPU加速? y / N, 默認: N: ").strip().lower() == "y"

config = OptimizationConfig(
symbol = symbol,
max_combinations = max_combinations,
use_gpu = use_gpu,
show_progress = True,
save_intermediate = True,
)

printf"\n📊 配置摘要:"
printf"股票: {config.symbol}"
print(f"策略數量: {lenstrategies}")
printf"每策略最大組合: {config.max_combinations}"
printf"GPU加速: {'是' if config.use_gpu else '否'}"
print"-" * 50

confirm = input("\n確認開始比較? Y / n: ").strip().lower()
if confirm == "n":
print"操作已取消"
return

try:

self.optimizer = ParameterOptimizerconfig
printf"\n🚀 開始多策略比較..."

start_time = time.time()
results = self.optimizer.compare_strategiessymbol, strategies
execution_time = time.time() - start_time

printf"\n✅ 比較完成，耗時: {execution_time:.2f}秒"

self._save_comparison_resultssymbol, strategies, results

except Exception as e:
print(f"❌ 比較失敗: {stre}")

input"\n按Enter返回主菜單..."

def _load_previous_resultsself:
"""載入歷史結果"""
self._print_header()
print"📂 載入歷史優化結果"
print"-" * 50

results_dir = Path"optimization_results"
if not results_dir.exists():
print"❌ 未找到優化結果目錄"
input"按Enter返回..."
return

# 獲取JSON文件列表
json_files = list(results_dir.glob"*.json")
if not json_files:
print"❌ 未找到優化結果文件"
input"按Enter返回..."
return

# 按修改時間排序，顯示最新的10個
json_files.sort(key = lambda x: x.stat().st_mtime, reverse = True)
recent_files = json_files[:10]

printf"\n📋 最近10個優化結果:"
for i, file in enumeraterecent_files, 1:    mtime = time.strftime(
"%Y-%m-%d %H:%M:%S", time.localtime(file.stat().st_mtime)
)
size = file.stat().st_size024 # KB
print(f"{i:2d}. {file.name} {mtime}, {size:.1f}KB")

try:    choice = int(
input(f"\n請選擇要載入的結果 (1-{lenrecent_files}): ").strip()
)
if 1 <= choice <= lenrecent_files:    selected_file = recent_files[choice - 1]

optimizer = ParameterOptimizer()
result = optimizer.load_results(strselected_file)

if result:    self.last_result = result
self.optimizer = optimizer
printf"\n✅ 成功載入結果: {selected_file.name}"
optimizer.display_resultsresult, detailed = True

self._show_result_optionsresult
else:
print"❌ 載入失敗"
else:
print"❌ 無效選擇"
except ValueError:
print"❌ 無效輸入"

input"\n按Enter返回主菜單..."

def _batch_optimizationself:
"""批量優化"""
self._print_header()
print"🚀 批量參數優化"
print"-" * 50

symbols_input = input(
"請輸入股票代碼列表，用逗號分隔 例如: 0700.HK,0941.HK,1398.HK: "
).strip()

if not symbols_input:
print"❌ 必須輸入至少一個股票代碼"
input"按Enter返回..."
return

symbols = [s.strip() for s in symbols_input.split"," if s.strip()]

strategies = ["RSI_MEAN_REVERSION", "MACD_CROSSOVER", "DUAL_MOVING_AVERAGE"]
printf"\n可用策略:"
for i, strategy in enumeratestrategies, 1:
printf"{i}. {strategy}"

try:    strategy_choice = int(input(f"請選擇策略 (1-{len(strategies)}): ").strip())
if 1 <= strategy_choice <= lenstrategies:    strategy = strategies[strategy_choice - 1]
else:
raise ValueError"Invalid choice"
except ValueError:
print"無效選擇，使用默認策略"
strategy = strategies[0]

max_combinations = self._get_int_input(
"每個股票的最大組合數 默認: 200: ", 200
)
use_gpu = input("使用GPU加速? y / N, 默認: N: ").strip().lower() == "y"

printf"\n🚀 批量優化配置:"
print(f"股票數量: {lensymbols}")
print(f"股票列表: {', '.joinsymbols}")
printf"策略: {strategy}"
printf"每股票最大組合: {max_combinations}"
printf"GPU加速: {'是' if use_gpu else '否'}"
print"-" * 50

confirm = (
input(f"\n確認開始批量優化 {lensymbols} 個股票? Y / n: ").strip().lower()
)
if confirm == "n":
print"操作已取消"
return

try:

config = OptimizationConfig(
strategy = strategy,
max_combinations = max_combinations,
use_gpu = use_gpu,
show_progress = True,
save_intermediate = True,
)

optimizer = ParameterOptimizerconfig
batch_results = {}

printf"\n🚀 開始批量優化..."
start_time = time.time()

for i, symbol in enumeratesymbols, 1:
print(f"\n[{i}/{lensymbols}] 正在優化: {symbol}")

try:    result = optimizer.run_optimization(symbol = symbol)
batch_results[symbol] = result
print(
f"✅ {symbol} 完成 - Sharpe: {result.best_performance.get'sharpe_ratio', 0:.3f}"
)
except Exception as e:
print(f"❌ {symbol} 失敗 - {stre}")

execution_time = time.time() - start_time

# 顯示批量結果摘要
printf"\n{'='*60}"
print"📊 批量優化結果摘要"
printf"{'='*60}"

if batch_results:    table_data = []
headers = ["股票", "最佳Sharpe", "總回報", "最大回撤", "優化時間秒"]

for symbol, result in batch_results.items():    perf = result.best_performance
table_data.append(
[
symbol,
f"{perf.get'sharpe_ratio', 0:.3f}",
f"{perf.get'total_return', 0:.2%}",
f"{perf.get'max_drawdown', 0:.2%}",
f"{result.optimization_time:.2f}",
]
)

if TABULATE_AVAILABLE:    print(tabulate(table_data, headers = headers, tablefmt="grid"))
else:
for row in table_data:
print(f" {' | '.joinrow}")

best_stock = max(
batch_results.items(),
key = lambda x: x[1].best_performance.get"sharpe_ratio", 0,
)
print(
f"\n🏆 最佳股票: {best_stock[0]} (Sharpe: {best_stock[1].best_performance.get'sharpe_ratio', 0:.3f})"
)

printf"\n✅ 批量優化完成，總耗時: {execution_time:.2f}秒"

self._save_batch_resultsbatch_results

except Exception as e:
print(f"❌ 批量優化失敗: {stre}")

input"\n按Enter返回主菜單..."

def _advanced_settingsself:
"""高級設置"""
self._print_header()
print"⚙️ 高級設置"
print"-" * 50

print"1. 系統信息"
print"2. 優化參數默認值"
print"3. 性能配置"
print"4. 導出設置"
print"5. 返回主菜單"

choice = input("\n請選擇設置類型 1 - 5: ").strip()

if choice == "1":
self._show_system_info()
elif choice == "2":
self._configure_defaults()
elif choice == "3":
self._configure_performance()
elif choice == "4":
self._configure_export()
elif choice == "5":
return
else:
print"❌ 無效選擇"

input"\n按Enter返回..."

def _show_system_infoself:
"""顯示系統信息"""
print"\n🖥️ 系統信息:"
print"-" * 30

try:
from src.utils.dependency_manager import DependencyManager

dep_manager = DependencyManager()
status = dep_manager.get_dependency_status()

print(
f"✅ 核心依賴狀態: {'完整' if status['all_required_available'] else '缺失'}"
)
print(
f"🔢 可選依賴: {status['optional_available']}/{status['optional_total']}"
)
printf"🚀 GPU可用: {'是' if status['gpu_available'] else '否'}"
printf"📊 VectorBT可用: {'是' if status['vectorbt_available'] else '否'}"

printf"\n🖥️ 系統平台: {status['system_info']['platform']}"
printf"🐍 Python版本: {status['system_info']['python_version']}"
print(f"💻 CPU核心數: {status['system_info'].get'processor', 'Unknown'}")

except Exception as e:
printf"❌ 獲取系統信息失敗: {e}"

def _configure_defaultsself:
"""配置默認值"""
print"\n🔧 配置默認優化參數:"
print"-" * 30
print"此功能將在未來版本中實現"

def _configure_performanceself:
"""配置性能設置"""
print"\n⚡ 性能配置:"
print"-" * 30
print"此功能將在未來版本中實現"

def _configure_exportself:
"""配置導出設置"""
print"\n💾 導出設置:"
print"-" * 30
print"此功能將在未來版本中實現"

def _view_optimization_historyself:
"""查看優化歷史"""
self._print_header()
print"📈 優化歷史記錄"
print"-" * 50

results_dir = Path"optimization_results"
if not results_dir.exists():
print"❌ 未找到優化結果目錄"
input"按Enter返回..."
return

# 獲取所有JSON文件
json_files = list(results_dir.glob"*.json")
if not json_files:
print"❌ 未找到優化歷史記錄"
input"按Enter返回..."
return

total_files = lenjson_files
total_size = sum(f.stat().st_size for f in json_files) / 1024024 # MB

printf"📊 歷史統計:"
printf" • 總優化次數: {total_files}"
printf" • 總文件大小: {total_size:.2f} MB"

strategy_count = {}
for file in json_files:
# 嘗試從文件名中提取策略信息
parts = file.stem.split"_"
if lenparts >= 2:    strategy = parts[-2]  # 倒數第二部分可能是策略名
strategy_count[strategy] = strategy_count.getstrategy, 0 + 1

if strategy_count:
printf"\n📈 策略使用次數:"
for strategy, count in sorted(
strategy_count.items(), key = lambda x: x[1], reverse = True
):
printf" • {strategy}: {count}次"

printf"\n🕒 最近10次優化:"
json_files.sort(key = lambda x: x.stat().st_mtime, reverse = True)
for i, file in enumeratejson_files[:10], 1:    mtime = time.strftime(
"%Y-%m-%d %H:%M:%S", time.localtime(file.stat().st_mtime)
)
print(f" {i:2d}. {file.name} {mtime}")

input"\n按Enter返回..."

def _export_resultsself:
"""導出結果"""
self._print_header()
print"💾 導出優化結果"
print"-" * 50

if not self.last_result:
print"❌ 沒有可導出的結果"
input"按Enter返回..."
return

print"選擇導出格式:"
print"1. JSON格式"
print("2. CSV格式 僅性能數據")
print"3. HTML報告"
print"4. 返回主菜單"

choice = input("\n請選擇導出格式 1 - 4: ").strip()

try:    if choice == "1":
self._export_json()
elif choice == "2":
self._export_csv()
elif choice == "3":
self._export_html()
elif choice == "4":
return
else:
print"❌ 無效選擇"
except Exception as e:
print(f"❌ 導出失敗: {stre}")

input"\n按Enter返回..."

def _export_jsonself:
"""導出JSON格式"""
timestamp = time.strftime"%Y%m%d_%H%M%S"
filename = f"optimization_export_{timestamp}.json"

with openfilename, "w", encoding="utf - 8" as f:
json.dump(
self.last_result.to_dict(), f, ensure_ascii = False, indent = 2, default = str
)

printf"✅ 已導出到: {filename}"

def _export_csvself:
"""導出CSV格式"""
# 實現CSV導出邏輯
print"CSV導出功能將在未來版本中實現"

def _export_htmlself:
"""導出HTML報告"""
# 實現HTML報告導出邏輯
print"HTML報告導出功能將在未來版本中實現"

def _get_custom_parameter_rangesself, strategy: str -> Dict[str, List]:
"""獲取自定義參數範圍"""
printf"\n🔧 設置 {strategy} 參數範圍:"
print"留空使用默認值"

param_ranges = {}

if strategy == "RSI_MEAN_REVERSION":    period_min = self._get_int_input("RSI週期最小值 (默認: 5): ", 5)
period_max = self._get_int_input("RSI週期最大值 默認: 50: ", 50)
period_step = self._get_int_input("RSI週期步長 默認: 2: ", 2)

param_ranges["period"] = rangeperiod_min, period_max + 1, period_step

oversold_levels = input(
"超賣水平，用逗號分隔 默認: 20,25,30,35,40: "
).strip()
if oversold_levels:    param_ranges["oversold"] = [
float(x.strip()) for x in oversold_levels.split","
]

overbought_levels = input(
"超買水平，用逗號分隔 默認: 60,65,70,75,80: "
).strip()
if overbought_levels:    param_ranges["overbought"] = [
float(x.strip()) for x in overbought_levels.split","
]

# 可以為其他策略添加類似的自定義邏輯

return param_ranges

def _get_optimization_metricself -> str:
"""獲取優化目標"""
metrics = [
"1", "sharpe_ratio", "Sharpe比率",
"2", "total_return", "總回報率",
("3", "max_drawdown", "最大回撤 越小越好"),
"4", "calmar_ratio", "Calmar比率",
"5", "sortino_ratio", "Sortino比率",
]

printf"\n🎯 選擇優化目標:"
for code, key, desc in metrics:
printf"{code}. {desc}"

try:    choice = int(input("請選擇優化目標 (1 - 5, 默認: 1): ").strip() or "1")
if 1 <= choice <= lenmetrics:
return metrics[choice - 1][1]
else:
return metrics[0][1]
except ValueError:
return metrics[0][1]

def _get_int_inputself, prompt: str, default: int -> int:
"""獲取整數輸入"""
while True:
try:    value_str = input(prompt).strip()
if not value_str:
return default
return intvalue_str
except ValueError:
print"❌ 請輸入有效的整數"

def _show_result_optionsself, result:
"""顯示結果操作選項"""
printf"\n🔧 結果操作選項:"
print"1. 📊 顯示詳細結果"
print"2. 💾 保存結果"
print"3. 📂 載入其他結果"
print"4. 🚀 基於最佳參數進行回測"
print"5. 📈 查看參數敏感性分析"
print"6. ⏭️ 跳過，返回主菜單"

choice = input("\n請選擇操作 1 - 6: ").strip()

try:    if choice == "1":
self.optimizer.display_resultsresult, detailed = True
elif choice == "2":
print"✅ 結果已自動保存"
elif choice == "3":
self._load_previous_results()
elif choice == "4":
self._run_backtest_with_best_paramsresult
elif choice == "5":
print"參數敏感性分析功能將在未來版本中實現"
elif choice == "6":
return
else:
print"❌ 無效選擇"
except Exception as e:
print(f"❌ 操作失敗: {stre}")

def _run_backtest_with_best_paramsself, result:
"""使用最佳參數運行回測"""
printf"\n🚀 使用最佳參數運行完整回測..."
printf"股票: {result.symbol}"
printf"策略: {result.strategy}"
printf"參數: {result.best_parameters}"

# 這裡可以實現完整的回測邏輯
print"完整回測功能將在未來版本中實現"

def _save_comparison_results(
self, symbol: str, strategies: List[str], results: Dict
):
"""保存比較結果"""
timestamp = time.strftime"%Y%m%d_%H%M%S"
filename = f"strategy_comparison_{symbol}_{timestamp}.json"

comparison_data = {
"symbol": symbol,
"strategies": strategies,
"timestamp": timestamp,
"results": {
strategy: result.to_dict() for strategy, result in results.items()
},
}

with openf"optimization_results/{filename}", "w", encoding="utf - 8" as f:    json.dump(comparison_data, f, ensure_ascii = False, indent = 2, default = str)

printf"✅ 比較結果已保存到: optimization_results/{filename}"

def _save_batch_resultsself, batch_results: Dict[str, Any]:
"""保存批量結果"""
timestamp = time.strftime"%Y%m%d_%H%M%S"
filename = f"batch_optimization_{timestamp}.json"

batch_data = {
"timestamp": timestamp,
"total_stocks": lenbatch_results,
"results": {
symbol: result.to_dict() for symbol, result in batch_results.items()
},
}

with openf"optimization_results/{filename}", "w", encoding="utf - 8" as f:    json.dump(batch_data, f, ensure_ascii = False, indent = 2, default = str)

printf"✅ 批量結果已保存到: optimization_results/{filename}"

def main():
"""主函數"""
try:    menu = OptimizationMenu()
menu.show_menu()
except KeyboardInterrupt:
print"\n\n👋 程序已退出"
except Exception as e:
print(f"\n❌ 程序發生錯誤: {stre}")

if __name__ == "__main__":
main()
