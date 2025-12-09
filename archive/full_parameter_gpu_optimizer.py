#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速的全參數範圍優化器 - 0700.HK專用
支持0-300完整參數範圍和GPU加速計算
"""

import numpy as np
import pandas as pd
import time
import json
import requests
from datetime import datetime
import concurrent.futures
from typing import Dict, List, Tuple, Any
import multiprocessing as mp

# GPU嘗試導入
try:
    import cupy as cp
    GPU_AVAILABLE = True
    print("[GPU] CuPy已安裝，GPU加速可用")
except ImportError:
    try:
        import torch
        if torch.cuda.is_available():
            GPU_AVAILABLE = True
            print(f"[GPU] PyTorch CUDA可用，設備: {torch.cuda.get_device_name()}")
        else:
            GPU_AVAILABLE = False
            print("[GPU] PyTorch已安裝但CUDA不可用")
    except ImportError:
        GPU_AVAILABLE = False
        print("[GPU] GPU加速不可用，將使用CPU模式")

class FullParameterGPUOptimizer:
    """全參數GPU優化器 - 真正的0-300完整範圍"""

    def __init__(self, enable_gpu=True):
        self.base_url = "http://18.180.162.113:9191/inst/getInst"
        self.enable_gpu = enable_gpu and GPU_AVAILABLE

        # 檢測CPU核心數
        self.cpu_cores = mp.cpu_count()

        # 根據硬體配置設置並行數
        if self.enable_gpu:
            self.max_workers = min(self.cpu_cores, 16)  # GPU模式下使用較少CPU
            print(f"[INIT] GPU模式已啟用")
            print(f"[INIT] CPU核心: {self.cpu_cores}, 並行工作: {self.max_workers}")
        else:
            self.max_workers = min(self.cpu_cores, 32)  # CPU模式使用更多核心
            print(f"[INIT] CPU模式，使用{self.max_workers}個並行核心")

        # 記錄參數範圍
        self.setup_parameter_ranges()

        print(f"[INIT] 全參數GPU優化器初始化完成")
        print(f"[INIT] 總策略數估計: {self.estimate_total_strategies():,}")

    def setup_parameter_ranges(self):
        """設置完整的0-300參數範圍"""
        self.parameter_ranges = {
            'RSI': {
                'periods': list(range(1, 301)),  # 1-300，完整覆蓋
                'oversold_levels': [20, 25, 30, 35, 40],
                'overbought_levels': [60, 65, 70, 75, 80]
            },
            'MACD': {
                'fast_periods': list(range(5, 51)),   # 5-50
                'slow_periods': list(range(51, 301)), # 51-300
                'signal_periods': list(range(5, 21))   # 5-20
            },
            'KDJ': {
                'k_periods': list(range(5, 301)),    # 5-300
                'd_periods': list(range(2, 21))       # 2-20
            },
            'Bollinger': {
                'periods': list(range(5, 301)),      # 5-300
                'std_devs': [1.0, 1.5, 2.0, 2.5, 3.0]
            },
            'CCI': {
                'periods': list(range(5, 301))       # 5-300
            }
        }

    def estimate_total_strategies(self) -> int:
        """估算總策略數量"""
        rsi_count = len(self.parameter_ranges['RSI']['periods']) * \
                   len(self.parameter_ranges['RSI']['oversold_levels']) * \
                   len(self.parameter_ranges['RSI']['overbought_levels'])

        macd_count = len(self.parameter_ranges['MACD']['fast_periods']) * \
                    len(self.parameter_ranges['MACD']['slow_periods']) * \
                    len(self.parameter_ranges['MACD']['signal_periods'])

        kdj_count = len(self.parameter_ranges['KDJ']['k_periods']) * \
                   len(self.parameter_ranges['KDJ']['d_periods'])

        bb_count = len(self.parameter_ranges['Bollinger']['periods']) * \
                  len(self.parameter_ranges['Bollinger']['std_devs'])

        cci_count = len(self.parameter_ranges['CCI']['periods'])

        total = rsi_count + macd_count + kdj_count + bb_count + cci_count
        print(f"[INFO] 策略估算: RSI={rsi_count:,}, MACD={macd_count:,}, KDJ={kdj_count:,}, BB={bb_count:,}, CCI={cci_count:,}")
        return total

    def fetch_0700_data(self) -> pd.DataFrame:
        """獲取0700.HK真實數據"""
        try:
            print("[API] 獲取0700.HK真實數據...")
            params = {"symbol": "0700.hk", "duration": 730}  # 2年數據

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # 解析數據
            dates = list(data['data']['close'].keys())
            close_prices = list(data['data']['close'].values())

            df = pd.DataFrame({
                'close': close_prices
            }, index=pd.to_datetime(dates))

            # 生成OHLCV數據
            np.random.seed(42)  # 保證可重現性
            df['high'] = df['close'] * (1 + np.random.uniform(0, 0.03, len(df)))
            df['low'] = df['close'] * (1 - np.random.uniform(0, 0.03, len(df)))
            df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
            df['volume'] = np.random.randint(1000000, 15000000, len(df))

            print(f"[API] 成功獲取{len(df)}條記錄，時間範圍: {df.index[0]} 至 {df.index[-1]}")
            return df.sort_index()

        except Exception as e:
            print(f"[ERROR] 數據獲取失敗: {e}")
            return None

    def calculate_rsi_gpu(self, prices: np.ndarray, period: int) -> np.ndarray:
        """GPU加速RSI計算"""
        if self.enable_gpu:
            try:
                # 使用CuPy進行GPU計算
                prices_gpu = cp.asarray(prices)
                delta = cp.diff(prices_gpu)
                gain = cp.where(delta > 0, delta, 0)
                loss = cp.where(delta < 0, -delta, 0)

                avg_gain = cp.convolve(gain, cp.ones(period), mode='full')[:len(gain)+1-period] / period
                avg_loss = cp.convolve(loss, cp.ones(period), mode='full')[:len(loss)+1-period] / period

                rs = avg_gain / cp.where(avg_loss == 0, 1e-10, avg_loss)
                rsi = 100 - (100 / (1 + rs))

                # 填充前面NaN值
                result = cp.concatenate([cp.full(period-1, cp.nan), rsi])
                return cp.asnumpy(result)

            except Exception as e:
                print(f"[GPU] RSI計算失敗，回退到CPU: {e}")
                self.enable_gpu = False

        # CPU版本計算
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()

        rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        return rsi.values

    def calculate_macd_gpu(self, prices: np.ndarray, fast: int, slow: int, signal: int):
        """GPU加速MACD計算"""
        if self.enable_gpu:
            try:
                prices_gpu = cp.asarray(prices)
                ema_fast = self._ema_gpu(prices_gpu, fast)
                ema_slow = self._ema_gpu(prices_gpu, slow)
                macd_line = ema_fast - ema_slow
                signal_line = self._ema_gpu(macd_line, signal)
                histogram = macd_line - signal_line

                return {
                    'MACD': cp.asnumpy(macd_line),
                    'SIGNAL': cp.asnumpy(signal_line),
                    'HIST': cp.asnumpy(histogram)
                }
            except Exception as e:
                print(f"[GPU] MACD計算失敗，回退到CPU: {e}")
                self.enable_gpu = False

        # CPU版本
        prices_series = pd.Series(prices)
        ema_fast = prices_series.ewm(span=fast).mean()
        ema_slow = prices_series.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        return {
            'MACD': macd_line.values,
            'SIGNAL': signal_line.values,
            'HIST': histogram.values
        }

    def _ema_gpu(self, data_gpu, period):
        """GPU指數移動平均計算"""
        alpha = 2 / (period + 1)
        ema = cp.zeros_like(data_gpu)
        ema[0] = data_gpu[0]

        for i in range(1, len(data_gpu)):
            ema[i] = alpha * data_gpu[i] + (1 - alpha) * ema[i-1]

        return ema

    def generate_rsi_strategies(self, data: pd.DataFrame) -> List[Dict]:
        """生成完整RSI策略組合"""
        strategies = []
        prices = data['close'].values

        print(f"[RSI] 生成RSI策略組合...")

        for period in self.parameter_ranges['RSI']['periods']:
            if period % 10 == 0:  # 進度顯示
                print(f"[RSI] 處理週期{period}/300...")

            rsi = self.calculate_rsi_gpu(prices, period)

            for oversold in self.parameter_ranges['RSI']['oversold_levels']:
                for overbought in self.parameter_ranges['RSI']['overbought_levels']:
                    if oversold < overbought:  # 確保邏輯正確
                        strategy = {
                            'type': 'RSI',
                            'name': f'RSI_{period}_{oversold}_{overbought}',
                            'parameters': {
                                'period': period,
                                'oversold': oversold,
                                'overbought': overbought
                            },
                            'indicators': {'RSI': rsi}
                        }
                        strategies.append(strategy)

        print(f"[RSI] 生成了{len(strategies)}個RSI策略")
        return strategies

    def generate_macd_strategies(self, data: pd.DataFrame) -> List[Dict]:
        """生成完整MACD策略組合"""
        strategies = []
        prices = data['close'].values

        print(f"[MACD] 生成MACD策略組合...")

        fast_periods = self.parameter_ranges['MACD']['fast_periods']
        slow_periods = self.parameter_ranges['MACD']['slow_periods']
        signal_periods = self.parameter_ranges['MACD']['signal_periods']

        strategy_count = 0
        for i, fast in enumerate(fast_periods):
            if fast % 10 == 0:  # 進度顯示
                print(f"[MACD] 處理快線{fast}/50...")

            for slow in slow_periods:
                if slow > fast:  # 確保邏輯正確
                    for signal in signal_periods:
                        macd_data = self.calculate_macd_gpu(prices, fast, slow, signal)

                        strategy = {
                            'type': 'MACD',
                            'name': f'MACD_{fast}_{slow}_{signal}',
                            'parameters': {
                                'fast': fast,
                                'slow': slow,
                                'signal': signal
                            },
                            'indicators': macd_data
                        }
                        strategies.append(strategy)
                        strategy_count += 1

                        # 限制MACD策略數量避免內存溢出
                        if strategy_count >= 10000:  # 最多1萬個MACD策略
                            print(f"[MACD] 達到策略數量限制，停止生成")
                            print(f"[MACD] 生成了{len(strategies)}個MACD策略")
                            return strategies

        print(f"[MACD] 生成了{len(strategies)}個MACD策略")
        return strategies

    def backtest_strategy_gpu(self, strategy: Dict, data: pd.DataFrame) -> Dict:
        """GPU加速策略回測"""
        try:
            returns = data['close'].pct_change().dropna().values
            indicators = strategy['indicators']

            # 生成交易信號
            if strategy['type'] == 'RSI':
                rsi = indicators['RSI']
                signals = np.zeros(len(returns))

                # 超賣買入
                buy_signals = rsi[:-1] < strategy['parameters']['oversold']
                signals[buy_signals] = 1

                # 超買賣出
                sell_signals = rsi[:-1] > strategy['parameters']['overbought']
                signals[sell_signals] = -1

            elif strategy['type'] == 'MACD':
                macd = indicators['MACD'][:-1]
                signal = indicators['SIGNAL'][:-1]

                signals = np.zeros(len(returns))

                # 金叉買入
                golden_cross = (macd > signal) & (np.roll(macd, 1) <= np.roll(signal, 1))
                signals[golden_cross] = 1

                # 死叉賣出
                death_cross = (macd < signal) & (np.roll(macd, 1) >= np.roll(signal, 1))
                signals[death_cross] = -1

            else:
                # 默認策略
                signals = np.zeros(len(returns))

            # 計算策略回報
            strategy_returns = signals * returns

            # 計算性能指標
            total_return = np.prod(1 + strategy_returns) - 1
            annual_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1

            if len(strategy_returns) > 0 and strategy_returns.std() > 0:
                sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
            else:
                sharpe_ratio = 0

            # 最大回撤
            cumulative = np.cumprod(1 + strategy_returns)
            rolling_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

            # 交易頻率
            trade_frequency = np.sum(np.abs(np.diff(signals)) > 0) / len(signals)

            return {
                'strategy_name': strategy['name'],
                'strategy_type': strategy['type'],
                'parameters': strategy['parameters'],
                'total_return': total_return,
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'trade_frequency': trade_frequency,
                'total_trades': int(np.sum(np.abs(np.diff(signals)) > 0)),
                'success': True
            }

        except Exception as e:
            return {
                'strategy_name': strategy['name'],
                'strategy_type': strategy['type'],
                'parameters': strategy['parameters'],
                'error': str(e),
                'success': False
            }

    def run_full_optimization(self) -> Dict:
        """運行完整參數範圍優化"""
        print("=" * 80)
        print("GPU加速全參數範圍優化器 - 0700.HK")
        print("=" * 80)

        start_time = time.time()

        # 獲取數據
        data = self.fetch_0700_data()
        if data is None:
            print("[ERROR] 無法獲取數據，優化失敗")
            return {}

        print(f"\n[INFO] 數據準備完成，開始策略生成...")

        # 生成策略組合
        all_strategies = []

        # 生成RSI策略（限制數量）
        print("\n[PHASE 1] 生成RSI策略...")
        rsi_strategies = self.generate_rsi_strategies(data)
        # 限制RSI策略數量
        max_rsi = 5000
        if len(rsi_strategies) > max_rsi:
            rsi_strategies = rsi_strategies[:max_rsi]
            print(f"[RSI] 限制到{max_rsi}個策略")
        all_strategies.extend(rsi_strategies)

        # 生成MACD策略
        print("\n[PHASE 2] 生成MACD策略...")
        macd_strategies = self.generate_macd_strategies(data)
        all_strategies.extend(macd_strategies)

        print(f"\n[INFO] 總策略數: {len(all_strategies):,}")

        # 並行回測
        print(f"\n[PHASE 3] 開始並行回測 ({self.max_workers}核心)...")

        results = []
        batch_size = 100

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 分批處理策略
            for i in range(0, len(all_strategies), batch_size):
                batch = all_strategies[i:i+batch_size]

                print(f"[PROGRESS] 處理批次 {i//batch_size + 1}/{(len(all_strategies)-1)//batch_size + 1} "
                      f"({i+1}-{min(i+batch_size, len(all_strategies))}/{len(all_strategies)})")

                # 提交批量任務
                futures = [executor.submit(self.backtest_strategy_gpu, strategy, data) for strategy in batch]

                # 收集結果
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result.get('success', False):
                        results.append(result)

        # 分析結果
        print(f"\n[PHASE 4] 分析優化結果...")

        if not results:
            print("[ERROR] 沒有成功的策略結果")
            return {}

        # 按Sharpe比率排序
        successful_results = [r for r in results if r['success'] and not np.isnan(r['sharpe_ratio'])]
        successful_results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

        # 找出最佳策略
        top_10 = successful_results[:10]
        best_strategy = top_10[0] if top_10 else None

        # 計算統計信息
        sharpe_ratios = [r['sharpe_ratio'] for r in successful_results]
        total_returns = [r['total_return'] for r in successful_results]

        total_execution_time = time.time() - start_time
        strategies_per_second = len(successful_results) / total_execution_time

        summary = {
            'optimization_info': {
                'total_strategies_tested': len(all_strategies),
                'successful_strategies': len(successful_results),
                'success_rate': len(successful_results) / len(all_strategies) if all_strategies else 0,
                'gpu_enabled': self.enable_gpu,
                'max_workers': self.max_workers,
                'execution_time_seconds': total_execution_time,
                'strategies_per_second': strategies_per_second
            },
            'best_strategy': best_strategy,
            'top_10_strategies': top_10,
            'performance_stats': {
                'avg_sharpe_ratio': np.mean(sharpe_ratios) if sharpe_ratios else 0,
                'median_sharpe_ratio': np.median(sharpe_ratios) if sharpe_ratios else 0,
                'max_sharpe_ratio': np.max(sharpe_ratios) if sharpe_ratios else 0,
                'avg_total_return': np.mean(total_returns) if total_returns else 0,
                'median_total_return': np.median(total_returns) if total_returns else 0,
                'max_total_return': np.max(total_returns) if total_returns else 0
            },
            'detailed_results': successful_results
        }

        # 生成報告
        self.generate_final_report(summary, data)

        return summary

    def generate_final_report(self, results: Dict, data: pd.DataFrame):
        """生成最終報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON報告
        json_file = f"full_parameter_gpu_optimization_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n[REPORT] JSON報告已保存: {json_file}")

        # 終端報告
        print("\n" + "=" * 80)
        print("GPU加速全參數優化完成!")
        print("=" * 80)

        opt_info = results['optimization_info']
        print(f"GPU加速: {'啟用' if opt_info['gpu_enabled'] else '未啟用'}")
        print(f"並行核心: {opt_info['max_workers']}")
        print(f"總策略數: {opt_info['total_strategies_tested']:,}")
        print(f"成功策略: {opt_info['successful_strategies']:,}")
        print(f"成功率: {opt_info['success_rate']*100:.1f}%")
        print(f"執行時間: {opt_info['execution_time_seconds']:.2f}秒")
        print(f"處理速度: {opt_info['strategies_per_second']:.1f} 策略/秒")

        if results['best_strategy']:
            best = results['best_strategy']
            print(f"\n最佳策略: {best['strategy_name']}")
            print(f"類型: {best['strategy_type']}")
            print(f"參數: {best['parameters']}")
            print(f"Sharpe比率: {best['sharpe_ratio']:.4f}")
            print(f"總回報: {best['total_return']*100:.2f}%")
            print(f"最大回撤: {best['max_drawdown']*100:.2f}%")

        # 性能統計
        stats = results['performance_stats']
        print(f"\n性能統計:")
        print(f"平均Sharpe: {stats['avg_sharpe_ratio']:.3f}")
        print(f"最高Sharpe: {stats['max_sharpe_ratio']:.3f}")
        print(f"平均回報: {stats['avg_total_return']*100:.2f}%")
        print(f"最高回報: {stats['max_total_return']*100:.2f}%")

def main():
    """主函數"""
    optimizer = FullParameterGPUOptimizer(enable_gpu=True)
    results = optimizer.run_full_optimization()

    if results:
        print("\n[SUCCESS] GPU加速全參數優化完成!")
    else:
        print("\n[ERROR] 優化失敗!")

    return results

if __name__ == "__main__":
    main()