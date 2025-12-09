# 提案: 放寬回測進場條件的全面參數優化系統

**OpenSpec ID**: `relaxed-entry-conditions`
**創建日期**: 2025-11-24
**狀態**: Draft
**負責人**: Penguin8n

## 🎯 問題定義

### 現有系統問題
通過分析現有的回測系統，發現以下關鍵問題：

#### 1. 進場條件過於嚴格
**問題**: 現有系統使用固定的進場條件，導致交易信號過少：
- **RSI策略**: 固定使用 `oversold=30, overbought=70`
- **信號生成**: 需要同時滿足多個嚴格條件才觸發交易
- **實際結果**: 很多策略組合幾乎沒有交易信號

#### 2. 參數覆蓋不完整
**問題**: 現有參數優化範圍有限：
- **RSI週期**: 通常只在10-50範圍測試
- **閾值設定**: oversold/overbought組合固定
- **遺漏機會**: 0-300完整範圍未充分探索

#### 3. 步長設定過粗
**問題**: 現有步長設定可能錯過最優參數：
- **週期步長**: 通常使用5或10，跳過了許多潛在最優點
- **閾值步長**: 5點間距可能遺漏最佳進場點

### 用戶需求
**核心需求**: 找出不同技術分析參數組合，0-300範圍，步長5，回測所有可能性

**具體要求**:
1. **完整覆蓋**: 0-300參數範圍，不遺漏任何可能性
2. **精確步長**: 步長5，平衡精度和計算效率
3. **放寬條件**: 降低進場門檻，增加交易信號
4. **全面回測**: 測試所有可能的參數組合

## 🎯 解決方案概述

### 設計原則
1. **完整覆蓋**: 0-300範圍，步長5，不遺漏任何潛在最優組合
2. **條件放寬**: 多層級進場條件，從嚴格到寬鬆全面測試
3. **智能過濾**: 基於交易頻率和表現的智能策略篩選
4. **性能優化**: 高效並行計算，支持大規模參數組合測試

### 解決策略

#### 核心改進：從固定條件到動態範圍
```
現有系統 (過於嚴格):
├── RSI: oversold=30, overbought=70 (固定值)
├── 週期: 10-50範圍 (有限)
└── 結果: 交易信號稀少

新系統 (放寬條件):
├── RSI: oversold=15-45 (範圍), overbought=55-85 (範圍)
├── 週期: 0-300完整範圍，步長5
├── 多層條件: 嚴格/中等/寬鬆三種進場策略
└── 結果: 全面覆蓋，不遺漏任何機會
```

#### 進場條件放寬策略
```python
# 三層進場條件系統
entry_conditions = {
    'strict': {      # 嚴格條件 (現有)
        'oversold_range': [25, 30, 35],
        'overbought_range': [65, 70, 75],
        'signal_strength': 'strong'
    },
    'moderate': {    # 中等條件 (新增)
        'oversold_range': [20, 25, 30, 35, 40],
        'overbought_range': [60, 65, 70, 75, 80],
        'signal_strength': 'moderate'
    },
    'relaxed': {     # 寬鬆條件 (新增)
        'oversold_range': [15, 20, 25, 30, 35, 40, 45],
        'overbought_range': [55, 60, 65, 70, 75, 80, 85],
        'signal_strength': 'relaxed'
    }
}
```

## 📊 解決方案描述

### 1. 完整參數空間探索

#### 0-300範圍，步長5的完整覆蓋
```python
class CompleteParameterSpace:
    """完整參數空間探索器 - 0-300範圍，步長5"""

    def __init__(self):
        # 完整的參數範圍定義
        self.parameter_ranges = {
            'rsi_period': list(range(5, 301, 5)),      # 5, 10, 15, ..., 300
            'macd_fast': list(range(5, 51, 5)),        # 5, 10, 15, ..., 50
            'macd_slow': list(range(55, 301, 5)),      # 55, 60, 65, ..., 300
            'macd_signal': list(range(5, 21, 5)),      # 5, 10, 15, 20
            'bb_period': list(range(5, 301, 5)),       # 5, 10, 15, ..., 300
            'bb_std': [1.5, 2.0, 2.5, 3.0],            # 布林帶標準差
            'kdj_k': list(range(5, 301, 5)),           # K週期: 5, 10, ..., 300
            'kdj_d': list(range(1, 21, 5)),            # D平滑: 1, 6, 11, 16
            'sma_short': list(range(5, 101, 5)),       # 短期SMA: 5, 10, ..., 100
            'sma_long': list(range(105, 301, 5))       # 長期SMA: 105, 110, ..., 300
        }

        self.entry_conditions = {
            'strict': {
                'oversold_levels': [25, 30, 35],
                'overbought_levels': [65, 70, 75]
            },
            'moderate': {
                'oversold_levels': [20, 25, 30, 35, 40],
                'overbought_levels': [60, 65, 70, 75, 80]
            },
            'relaxed': {
                'oversold_levels': [15, 20, 25, 30, 35, 40, 45],
                'overbought_levels': [55, 60, 65, 70, 75, 80, 85]
            }
        }

    def generate_all_combinations(self, strategy_type='all'):
        """生成所有可能的參數組合"""

        # RSI策略組合
        rsi_combinations = []
        for period in self.parameter_ranges['rsi_period']:
            for condition_type, levels in self.entry_conditions.items():
                for oversold in levels['oversold_levels']:
                    for overbought in levels['overbought_levels']:
                        if oversold < overbought:  # 確保邏輯正確
                            rsi_combinations.append({
                                'strategy': 'RSI',
                                'period': period,
                                'oversold': oversold,
                                'overbought': overbought,
                                'condition_type': condition_type
                            })

        # MACD策略組合
        macd_combinations = []
        for fast in self.parameter_ranges['macd_fast']:
            for slow in self.parameter_ranges['macd_slow']:
                if fast < slow:  # 確保邏輯正確
                    for signal in self.parameter_ranges['macd_signal']:
                        macd_combinations.append({
                            'strategy': 'MACD',
                            'fast': fast,
                            'slow': slow,
                            'signal': signal,
                            'condition_type': 'standard'
                        })

        # KDJ策略組合
        kdj_combinations = []
        for k_period in self.parameter_ranges['kdj_k']:
            for d_period in self.parameter_ranges['kdj_d']:
                kdj_combinations.append({
                    'strategy': 'KDJ',
                    'k_period': k_period,
                    'd_period': d_period,
                    'condition_type': 'standard'
                })

        # 布林帶策略組合
        bb_combinations = []
        for period in self.parameter_ranges['bb_period']:
            for std in self.parameter_ranges['bb_std']:
                bb_combinations.append({
                    'strategy': 'BOLLINGER_BANDS',
                    'period': period,
                    'std_dev': std,
                    'condition_type': 'standard'
                })

        return {
            'RSI': rsi_combinations,
            'MACD': macd_combinations,
            'KDJ': kdj_combinations,
            'BOLLINGER_BANDS': bb_combinations
        }

    def get_total_combinations_count(self):
        """計算總策略組合數量"""
        combinations = self.generate_all_combinations()
        total = sum(len(combos) for combos in combinations.values())
        return total
```

### 2. 放寬的進場條件引擎

#### 多層級進場信號生成
```python
class RelaxedEntryConditionEngine:
    """放寬的進場條件引擎"""

    def __init__(self, condition_type='moderate'):
        self.condition_type = condition_type
        self.min_trade_frequency = 0.1  # 最小交易頻率10%

    def generate_rsi_signals(self, rsi_series, oversold, overbought, condition_type='moderate'):
        """生成RSI交易信號 - 支持多種條件類型"""

        if condition_type == 'strict':
            # 嚴格條件：需要明確穿越邊界
            entries = rsi_series < oversold
            exits = rsi_series > overbought

        elif condition_type == 'moderate':
            # 中等條件：接近邊界即可觸發
            oversold_buffer = 5
            overbought_buffer = 5

            entries = rsi_series < (oversold + oversold_buffer)
            exits = rsi_series > (overbought - overbought_buffer)

        elif condition_type == 'relaxed':
            # 寬鬆條件：大幅放寬進場門檻
            oversold_buffer = 10
            overbought_buffer = 10

            entries = rsi_series < (oversold + oversold_buffer)
            exits = rsi_series > (overbought - overbought_buffer)

        return entries, exits

    def generate_macd_signals(self, macd_line, signal_line, condition_type='moderate'):
        """生成MACD交易信號"""

        if condition_type == 'strict':
            # 嚴格條件：明確的金叉死叉
            entries = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
            exits = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

        elif condition_type == 'moderate':
            # 中等條件：接近零軸也考慮
            zero_cross_buffer = 0.1
            entries = ((macd_line > signal_line) &
                      (macd_line.shift(1) <= signal_line.shift(1))) | \
                     ((macd_line > zero_cross_buffer) & (macd_line.shift(1) <= zero_cross_buffer))
            exits = ((macd_line < signal_line) &
                    (macd_line.shift(1) >= signal_line.shift(1))) | \
                   ((macd_line < -zero_cross_buffer) & (macd_line.shift(1) >= -zero_cross_buffer))

        elif condition_type == 'relaxed':
            # 寬鬆條件：考慮趨勢方向
            trend_threshold = 0.05
            entries = (macd_line > signal_line) | (macd_line > trend_threshold)
            exits = (macd_line < signal_line) | (macd_line < -trend_threshold)

        return entries, exits

    def validate_signal_frequency(self, entries, exits, min_periods=252):
        """驗證交易信號頻率是否足夠"""

        total_periods = len(entries)
        if total_periods < min_periods:
            return False, "數據期間不足"

        # 計算交易信號數量
        entry_signals = entries.sum()
        exit_signals = exits.sum()

        # 計算交易頻率
        entry_frequency = entry_signals / total_periods
        exit_frequency = exit_signals / total_periods

        # 檢查是否達到最小交易頻率
        if entry_frequency < self.min_trade_frequency:
            return False, f"進場信號過少: {entry_frequency:.2%} < {self.min_trade_frequency:.2%}"

        if exit_frequency < self.min_trade_frequency:
            return False, f"出場信號過少: {exit_frequency:.2%} < {self.min_trade_frequency:.2%}"

        return True, f"信號頻率正常: 進場{entry_frequency:.2%}, 出場{exit_frequency:.2%}"
```

### 3. 高性能多進程回測執行引擎

#### 基於實際驗證的多進程架構
```python
import multiprocessing as mp
import concurrent.futures
import psutil
import time
from typing import Dict, List, Any
import numpy as np

class AdvancedMultiProcessBacktestEngine:
    """高性能多進程回測引擎 - 基於實際驗證的32核並行架構"""

    def __init__(self, max_workers=None):
        # 智能檢測並行核心數
        self.max_workers = max_workers or min(32, mp.cpu_count())
        self.parameter_space = CompleteParameterSpace()
        self.entry_engine = RelaxedEntryConditionEngine()
        self.sharpe_calculator = ProfessionalSharpeCalculator()

        # 進程池配置
        self.process_config = {
            'max_workers': self.max_workers,
            'mp_context': mp.get_context('spawn'),  # Windows兼容
            'initializer': self._worker_init,
            'timeout_per_task': 120,  # 120秒超時
            'chunk_size': 1000,       # 批次大小
            'memory_limit': '2GB'     # 每進程內存限制
        }

        print(f"[INIT] 高性能多進程回測引擎")
        print(f"[INIT] 檢測到CPU核心: {mp.cpu_count()}核")
        print(f"[INIT] 使用並行核心: {self.max_workers}核")
        print(f"[INIT] 內存總量: {psutil.virtual_memory().total / (1024**3):.1f}GB")
        print(f"[INIT] 進程上下文: {self.process_config['mp_context']}")

        # 計算總組合數量
        total_combinations = self.parameter_space.get_total_combinations_count()
        print(f"[INIT] 總策略組合: {total_combinations:,}")
        print(f"[INIT] 預估處理時間: {total_combinations/self.max_workers/60:.1f}分鐘")

    def _worker_init(self):
        """工作進程初始化"""
        # 設置進程優先級
        try:
            import os
            os.nice(10)  # 降低優先級，避免影響系統
        except:
            pass

        # 初始化進程級別的緩存
        import functools
        from functools import lru_cache

        # 預加載常用模塊
        import numpy as np
        import pandas as pd
        from professional_sharpe_calculator import ProfessionalSharpeCalculator

    def run_comprehensive_optimization(self, stock_data, government_data):
        """執行全面參數優化 - 智能分批並行處理"""

        print("\n" + "="*80)
        print("🚀 啟動全面參數優化系統")
        print("="*80)

        start_time = time.time()

        # 生成所有參數組合
        all_combinations = self.parameter_space.generate_all_combinations()

        # 準備多進程任務
        all_tasks = self._prepare_tasks(all_combinations, stock_data, government_data)

        print(f"\n[INFO] 任務準備完成:")
        print(f"       • RSI策略: {len(all_tasks['RSI']):,}個任務")
        print(f"       • MACD策略: {len(all_tasks['MACD']):,}個任務")
        print(f"       • KDJ策略: {len(all_tasks['KDJ']):,}個任務")
        print(f"       • 布林帶策略: {len(all_tasks['BOLLINGER_BANDS']):,}個任務")
        print(f"       • 總任務數: {sum(len(tasks) for tasks in all_tasks.values()):,}")

        # 分策略類型並行執行
        all_results = {}

        for strategy_type, tasks in all_tasks.items():
            print(f"\n[PROCESS] 開始處理 {strategy_type} 策略...")
            results = self._execute_strategy_batch(strategy_type, tasks)
            all_results[strategy_type] = results

            # 即時結果摘要
            if results:
                best_sharpe = max(r.get('sharpe_ratio', 0) for r in results)
                avg_sharpe = np.mean([r.get('sharpe_ratio', 0) for r in results])
                print(f"         ✓ 完成 {len(results)}個策略，最佳Sharpe: {best_sharpe:.3f}")
                print(f"         ✓ 平均Sharpe: {avg_sharpe:.3f}")

        # 合併和排序所有結果
        final_results = []
        for strategy_type, results in all_results.items():
            final_results.extend(results)

        # 按Sharpe比率排序
        final_results.sort(key=lambda x: x.get('sharpe_ratio', -999), reverse=True)

        # 性能統計
        end_time = time.time()
        execution_time = end_time - start_time
        total_tasks = sum(len(tasks) for tasks in all_tasks.values())
        success_rate = len(final_results) / total_tasks * 100

        print("\n" + "="*80)
        print("📊 優化完成統計")
        print("="*80)
        print(f"執行時間: {execution_time:.2f}秒 ({execution_time/60:.1f}分鐘)")
        print(f"成功策略: {len(final_results):,}/{total_tasks:,} ({success_rate:.1f}%)")
        print(f"處理速度: {total_tasks/execution_time:.1f} 策略/秒")
        print(f"並行效率: {self.max_workers * total_tasks/execution_time/60:.1f} 策略/核心/分鐘")

        # 最佳策略展示
        if final_results:
            print(f"\n🏆 前5名最佳策略:")
            for i, result in enumerate(final_results[:5], 1):
                print(f"   {i}. {result['strategy_name']}")
                print(f"      Sharpe: {result['sharpe_ratio']:.3f}, "
                      f"回報: {result['total_return']:.2%}, "
                      f"回撤: {result['max_drawdown']:.2%}")

        return final_results

    def _prepare_tasks(self, all_combinations, stock_data, government_data):
        """準備多進程任務 - 數據序列化優化"""

        # 將大型數據轉換為更高效的格式
        stock_data_serializable = {
            'close': stock_data['close'].values,
            'dates': stock_data.index.tolist() if hasattr(stock_data.index, 'tolist') else list(range(len(stock_data))),
            'length': len(stock_data)
        }

        government_data_serializable = {
            key: df.values if hasattr(df, 'values') else df
            for key, df in government_data.items()
        }

        all_tasks = {}

        for strategy_type, combinations in all_combinations.items():
            tasks = []
            for combo in combinations:
                task = {
                    'strategy': strategy_type,
                    'params': combo,
                    'stock_data': stock_data_serializable,
                    'government_data': government_data_serializable,
                    'task_id': f"{strategy_type}_{hash(str(combo)) % 1000000}"
                }
                tasks.append(task)

            all_tasks[strategy_type] = tasks

        return all_tasks

    def _execute_strategy_batch(self, strategy_type, tasks):
        """執行單個策略類型的批次任務"""

        results = []
        completed = 0
        failed = 0

        # 使用進程池執行
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers,
            mp_context=self.process_config['mp_context'],
            initializer=self._worker_init
        ) as executor:

            # 提交所有任務
            future_to_task = {
                executor.submit(self._execute_single_backtest_optimized, task): task
                for task in tasks
            }

            # 收集結果
            for future in concurrent.futures.as_completed(future_to_task, timeout=300):
                task = future_to_task[future]
                completed += 1

                try:
                    result = future.result(timeout=self.process_config['timeout_per_task'])
                    if result and isinstance(result, dict):
                        results.append(result)
                    else:
                        failed += 1

                except concurrent.futures.TimeoutError:
                    failed += 1
                    print(f"[TIMEOUT] {strategy_type} 任務超時: {task['task_id']}")

                except Exception as e:
                    failed += 1
                    # 避免打印過多錯誤信息
                    if failed <= 5:
                        print(f"[ERROR] {strategy_type} 任務失敗: {str(e)[:100]}")

                # 進度報告
                if completed % 500 == 0 or completed == len(tasks):
                    progress = completed / len(tasks) * 100
                    print(f"[PROGRESS] {strategy_type}: {completed:,}/{len(tasks):,} ({progress:.1f}%) - "
                          f"成功: {len(results)}, 失敗: {failed}")

        # 最終統計
        if failed > 0:
            print(f"[WARNING] {strategy_type} 失敗任務: {failed}個")

        return results

    @staticmethod
    def _execute_single_backtest_optimized(task):
        """優化的單個回測任務執行 - 靜態方法避免序列化問題"""

        try:
            strategy_type = task['strategy']
            params = task['params']
            stock_data_raw = task['stock_data']
            government_data_raw = task['government_data']

            # 重構數據對象
            import pandas as pd
            stock_data = pd.DataFrame({
                'close': stock_data_raw['close']
            })

            government_data = {
                key: pd.DataFrame(data) if isinstance(data, np.ndarray) else data
                for key, data in government_data_raw.items()
            }

            # 根據策略類型執行回測
            if strategy_type == 'RSI':
                return AdvancedMultiProcessBacktestEngine._backtest_rsi_strategy_optimized(
                    params, stock_data, government_data
                )
            elif strategy_type == 'MACD':
                return AdvancedMultiProcessBacktestEngine._backtest_macd_strategy_optimized(
                    params, stock_data, government_data
                )
            elif strategy_type == 'KDJ':
                return AdvancedMultiProcessBacktestEngine._backtest_kdj_strategy_optimized(
                    params, stock_data, government_data
                )
            elif strategy_type == 'BOLLINGER_BANDS':
                return AdvancedMultiProcessBacktestEngine._backtest_bb_strategy_optimized(
                    params, stock_data, government_data
                )
            else:
                return None

        except Exception as e:
            # 返回錯誤信息而不是直接拋出異常
            return {
                'strategy_type': strategy_type,
                'error': str(e),
                'params': params,
                'success': False
            }

    @staticmethod
    def _backtest_rsi_strategy_optimized(params, stock_data, government_data):
        """優化的RSI策略回測"""

        import numpy as np

        period = params['period']
        oversold = params['oversold']
        overbought = params['overbought']
        condition_type = params['condition_type']

        # 快速RSI計算
        close_prices = stock_data['close'].values
        rsi = AdvancedMultiProcessBacktestEngine._calculate_rsi_fast(close_prices, period)

        # 生成交易信號
        entries, exits = AdvancedMultiProcessBacktestEngine._generate_rsi_signals_fast(
            rsi, oversold, overbought, condition_type
        )

        # 驗證信號頻率
        total_periods = len(entries)
        entry_frequency = entries.sum() / total_periods
        exit_frequency = exits.sum() / total_periods

        if entry_frequency < 0.1 or exit_frequency < 0.1:
            return None

        # 計算回測結果
        returns = AdvancedMultiProcessBacktestEngine._calculate_returns_fast(
            close_prices, entries, exits
        )

        if len(returns) == 0:
            return None

        # 計算性能指標
        sharpe_ratio = AdvancedMultiProcessBacktestEngine._calculate_sharpe_fast(returns)
        max_drawdown = AdvancedMultiProcessBacktestEngine._calculate_max_drawdown_fast(returns)
        total_return = (1 + returns).prod() - 1

        # 計算質量分數
        quality_score = (
            min(sharpe_ratio * 20, 40) +  # Sharpe權重40%
            min(total_return * 50, 30) +   # 回報權重30%
            min((1 + max_drawdown) * 20, 20) +  # 回撤權重20%
            min(entry_frequency * 100, 10)  # 頻率權重10%
        )

        return {
            'strategy_type': 'RSI',
            'strategy_name': f"RSI_{period}_{oversold}_{overbought}_{condition_type}",
            'params': params,
            'sharpe_ratio': sharpe_ratio,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'trade_frequency': entry_frequency,
            'quality_score': quality_score,
            'success': True
        }

    @staticmethod
    def _calculate_rsi_fast(prices, period):
        """快速RSI計算 - 向量化實現"""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.zeros_like(prices)
        avg_loss = np.zeros_like(prices)

        if len(gain) >= period:
            avg_gain[period] = np.mean(gain[:period])
            avg_loss[period] = np.mean(loss[:period])

            for i in range(period + 1, len(prices)):
                avg_gain[i] = (avg_gain[i-1] * (period-1) + gain[i-1]) / period
                avg_loss[i] = (avg_loss[i-1] * (period-1) + loss[i-1]) / period

            rs = avg_gain[period:] / (avg_loss[period:] + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            return np.concatenate([[np.nan] * period, rsi])

        return np.full(len(prices), np.nan)

    @staticmethod
    def _generate_rsi_signals_fast(rsi, oversold, overbought, condition_type):
        """快速RSI信號生成"""

        if condition_type == 'strict':
            entries = rsi < oversold
            exits = rsi > overbought
        elif condition_type == 'moderate':
            entries = rsi < (oversold + 5)
            exits = rsi > (overbought - 5)
        else:  # relaxed
            entries = rsi < (oversold + 10)
            exits = rsi > (overbought - 10)

        return entries, exits

    @staticmethod
    def _calculate_returns_fast(prices, entries, exits):
        """快速回報計算"""
        positions = np.zeros_like(prices)

        # 簡化的進出場邏輯
        for i in range(1, len(positions)):
            if entries.iloc[i] if hasattr(entries, 'iloc') else entries[i]:
                positions[i] = 1
            elif (exits.iloc[i] if hasattr(exits, 'iloc') else exits[i]) and positions[i-1] > 0:
                positions[i] = 0
            else:
                positions[i] = positions[i-1]

        # 計算日收益率
        price_returns = np.diff(np.log(prices))
        strategy_returns = positions[1:] * price_returns

        return strategy_returns

    @staticmethod
    def _calculate_sharpe_fast(returns, risk_free_rate=0.03):
        """快速Sharpe計算"""
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate/252
        if np.std(excess_returns) == 0:
            return 0.0

        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

    @staticmethod
    def _calculate_max_drawdown_fast(returns):
        """快速最大回撤計算"""
        if len(returns) == 0:
            return 0.0

        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        return np.min(drawdowns)

    def _execute_single_backtest(self, task):
        """執行單個回測任務"""

        try:
            strategy_type = task['strategy']
            params = task['params']
            stock_data = task['stock_data']
            government_data = task['government_data']

            # 根據策略類型執行不同的回測邏輯
            if strategy_type == 'RSI':
                return self._backtest_rsi_strategy(params, stock_data, government_data)
            elif strategy_type == 'MACD':
                return self._backtest_macd_strategy(params, stock_data, government_data)
            elif strategy_type == 'KDJ':
                return self._backtest_kdj_strategy(params, stock_data, government_data)
            elif strategy_type == 'BOLLINGER_BANDS':
                return self._backtest_bb_strategy(params, stock_data, government_data)
            else:
                return None

        except Exception as e:
            print(f"[ERROR] 回測失敗 {task['strategy']}: {e}")
            return None

    def _backtest_rsi_strategy(self, params, stock_data, government_data):
        """RSI策略回測"""

        period = params['period']
        oversold = params['oversold']
        overbought = params['overbought']
        condition_type = params['condition_type']

        # 計算RSI
        rsi = self._calculate_rsi(stock_data['close'], period)

        # 生成交易信號
        entries, exits = self.entry_engine.generate_rsi_signals(
            rsi, oversold, overbought, condition_type
        )

        # 驗證信號頻率
        is_valid, message = self.entry_engine.validate_signal_frequency(entries, exits)
        if not is_valid:
            return None  # 信號過少，跳過此策略

        # 執行回測
        returns = self._calculate_portfolio_returns(
            stock_data['close'], entries, exits
        )

        # 計算性能指標
        sharpe_ratio = self.sharpe_calculator.calculate_sharpe_ratio(
            returns, risk_free_rate=0.03
        )

        max_drawdown = self._calculate_max_drawdown(returns)
        total_return = (1 + returns).prod() - 1

        return {
            'strategy_type': 'RSI',
            'strategy_name': f"RSI_{period}_{oversold}_{overbought}_{condition_type}",
            'params': params,
            'sharpe_ratio': sharpe_ratio,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'trade_frequency': entries.sum() / len(entries),
            'quality_score': self._calculate_quality_score(sharpe_ratio, total_return, max_drawdown)
        }
```

### 4. 結果分析和篩選系統

#### 智能策略評估
```python
class StrategyAnalyzer:
    """策略分析和篩選系統"""

    def __init__(self):
        self.performance_weights = {
            'sharpe_ratio': 0.4,
            'total_return': 0.3,
            'max_drawdown': 0.2,
            'trade_frequency': 0.1
        }

    def analyze_comprehensive_results(self, results):
        """分析全面回測結果"""

        if not results:
            return {"error": "沒有成功策略"}

        # 按策略類型分組
        strategy_groups = {}
        for result in results:
            strategy_type = result['strategy_type']
            if strategy_type not in strategy_groups:
                strategy_groups[strategy_type] = []
            strategy_groups[strategy_type].append(result)

        # 分析每種策略類型
        analysis = {
            'summary': self._generate_summary(results),
            'by_strategy_type': {},
            'top_strategies': results[:20],  # 前20個最佳策略
            'parameter_analysis': self._analyze_parameters(results),
            'entry_condition_analysis': self._analyze_entry_conditions(results)
        }

        # 詳細分析每種策略類型
        for strategy_type, strategies in strategy_groups.items():
            analysis['by_strategy_type'][strategy_type] = {
                'count': len(strategies),
                'best_strategy': max(strategies, key=lambda x: x['sharpe_ratio']),
                'average_sharpe': np.mean([s['sharpe_ratio'] for s in strategies]),
                'sharpe_distribution': self._analyze_distribution([s['sharpe_ratio'] for s in strategies])
            }

        return analysis

    def _generate_summary(self, results):
        """生成結果摘要"""

        sharpe_ratios = [r['sharpe_ratio'] for r in results]
        total_returns = [r['total_return'] for r in results]
        max_drawdowns = [r['max_drawdown'] for r in results]

        return {
            'total_strategies_tested': len(results),
            'best_sharpe_ratio': max(sharpe_ratios),
            'average_sharpe_ratio': np.mean(sharpe_ratios),
            'sharpe_ratio_std': np.std(sharpe_ratios),
            'best_total_return': max(total_returns),
            'average_total_return': np.mean(total_returns),
            'worst_max_drawdown': min(max_drawdowns),
            'average_max_drawdown': np.mean(max_drawdowns),
            'high_quality_strategies': len([r for r in results if r['quality_score'] > 70]),
            'excellent_strategies': len([r for r in results if r['quality_score'] > 85])
        }
```

## 🎯 實施計劃

### Phase 1: 核心引擎開發 (2天)
**目標**: 實現完整的0-300範圍參數空間和放寬進場條件

- **任務1**: 開發CompleteParameterSpace類，實現0-300範圍步長5的完整覆蓋
- **任務2**: 實現RelaxedEntryConditionEngine，支持嚴格/中等/寬鬆三種進場條件
- **任務3**: 開發ComprehensiveBacktestEngine，支持大規模並行回測
- **任務4**: 集成現有政府數據和股票數據API

### Phase 2: 回測邏輯實現 (2天)
**目標**: 實現各種技術分析策略的完整回測邏輯

- **任務1**: 實現RSI策略的完整參數回測（0-300範圍）
- **任務2**: 實現MACD策略的完整參數回測
- **任務3**: 實現KDJ策略的完整參數回測
- **任務4**: 實現布林帶策略的完整參數回測
- **任務5**: 添加交易頻率驗證和信號質量檢查

### Phase 3: 性能優化和並行處理 (1天)
**目標**: 優化系統性能，支持大規模計算

- **任務1**: 優化並行處理邏輯，提高計算效率
- **任務2**: 實現智能內存管理和緩存機制
- **任務3**: 添加進度監控和性能統計
- **任務4**: 實現錯誤處理和恢復機制

### Phase 4: 結果分析和可視化 (1天)
**目標**: 提供全面的結果分析和可視化功能

- **任務1**: 開發StrategyAnalyzer，實現智能策略分析
- **任務2**: 實現參數敏感性分析
- **任務3**: 添加進場條件效果對比分析
- **任務4**: 生成綜合分析報告和可視化圖表

## ✅ 驗收標準

### 功能完整性驗收
- [ ] **完整參數覆蓋**: 0-300範圍，步長5，無遺漏
- [ ] **多層進場條件**: 支持嚴格/中等/寬鬆三種策略
- [ ] **四大策略**: RSI, MACD, KDJ, 布林帶完整實現
- [ ] **信號頻率驗證**: 確保每個策略有足夠的交易信號
- [ ] **性能監控**: 實時進度和性能統計

### 性能指標驗收
- [ ] **計算效率**: 處理速度 > 200 策略/秒
- [ ] **成功率**: > 80%的策略組合成功執行
- [ ] **內存效率**: 支持>100,000個策略組合的處理
- [ ] **並行效率**: 32核並行利用率 > 90%

### 結果質量驗收
- [ ] **策略發現**: 至少發現10個Sharpe > 2.0的優秀策略
- [ ] **參數優化**: 提供最佳參數組合的詳細分析
- [ ] **進場條件分析**: 證明放寬條件的有效性
- [ ] **綜合報告**: 提供完整的分析報告和可視化

## 🎊 預期收益

### 策略發現收益
- **參數空間**: 增加10倍的參數組合覆蓋範圍
- **交易信號**: 增加5-10倍的有效交易信號
- **優質策略**: 預計發現20-50個高質量策略組合
- **Sharpe提升**: 預計最佳策略Sharpe提升30-50%

### 系統能力收益
- **完整覆蓋**: 0-300範圍，步長5，無遺漏任何機會
- **智能過濾**: 自動識別和過濾低頻率策略
- **性能監控**: 實時監控和優化系統性能
- **可擴展性**: 易於添加新的策略類型和數據源

### 用戶價值收益
- **全面探索**: 不再遺漏任何潛在的最優參數組合
- **效率提升**: 大幅減少手動參數調試時間
- **決策支持**: 提供數據驅動的參數選擇依據
- **風險控制**: 通過多條件測試降低策略風險

## ⚠️ 風險分析

### 計算風險 (中等風險)
- **計算複雜度**: 0-300範圍可能導致數十萬個策略組合
- **執行時間**: 大規模計算可能需要較長時間
- **內存使用**: 高並行可能消耗大量內存

**緩解措施**:
- 實現智能任務分批和內存管理
- 添加進度保存和恢復機制
- 提供計算資源監控和限制

### 信號質量風險 (低風險)
- **過度放寬**: 可能導致過多無效交易信號
- **過度擬合**: 大規模參數測試可能導致過度擬合
- **數據稀疏**: 某些參數組合可能缺乏足夠數據支持

**緩解措施**:
- 實現多層信號質量驗證
- 添加交叉驗證和樣本外測試
- 設置最小交易頻率閾值

## 📋 實施前提

### 技術要求
- **Python 3.9+**: 現有環境已滿足
- **並行處理**: 32核CPU環境，現有已具備
- **內存**: 16GB+ RAM支持大規模計算
- **存儲**: 足夠空間存儲大量回測結果

### 數據要求
- **股票數據**: 現有真實港股數據已滿足
- **政府數據**: 現有9個數據源已完整
- **數據質量**: 需要確保數據完整性和一致性

### 資源要求
- **開發時間**: 6個工作日
- **測試時間**: 2個工作日
- **計算資源**: 32核並行，預計24-48小時計算時間

## 📝 相關資料

### 現有成功案例
- `massive_nonprice_ta_optimizer.py` - 現有優化器基礎
- `relaxed_kdj_parameter_optimizer.py` - 放寬條件的初步嘗試
- MB_KDJ_[10,2]策略 - Sharpe 3.672的成功案例

### 技術參考
- VectorBT高性能回測框架
- Python多進程並行處理最佳實踐
- 技術分析指標計算標準方法

---

**審查狀態**: 待審查
**實施狀態**: 準備就緒
**最後更新**: 2025-11-24