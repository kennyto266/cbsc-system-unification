#!/usr/bin/env python3
"""
Walk-Forward Analysis Framework
走前分析框架

Professional walk-forward analysis for strategy validation
專業走前分析用於策略驗證
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta
import time

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available")

logger = logging.getLogger(__name__)

@dataclass
class WalkForwardConfig:
    """走前分析配置"""
    # 窗口參數
    window_size: int = 252  # 優化窗口大小 (交易日)
    step_size: int = 63     # 步長 (交易日)
    test_size: int = 42     # 測試窗口大小 (交易日)

    # 策略參數
    strategy: str = "RSI_MEAN_REVERSION"
    param_ranges: Dict[str, Any] = field(default_factory=lambda: {
        'period': [10, 14, 20, 30],
        'oversold': [20, 25, 30, 35],
        'overbought': [65, 70, 75, 80]
    })

    # 優化設置
    optimization_metric: str = "sharpe_ratio"
    max_combinations: int = 100

    # 性能設置
    enable_parallel: bool = True
    max_workers: int = 4

    # 回測設置
    initial_cash: float = 100000
    fees: float = 0.001
    slippage: float = 0.0005

@dataclass
class WalkForwardResult:
    """走前分析結果"""
    strategy: str
    total_periods: int
    window_size: int
    step_size: int
    test_size: int

    # 樣本外性能
    out_of_sample_return: float
    out_of_sample_sharpe: float
    out_of_sample_volatility: float
    out_of_sample_max_dd: float

    # 統計分析
    mean_return: float
    std_return: float
    mean_sharpe: float
    std_sharpe: float
    positive_periods: int
    positive_periods_ratio: float

    # 參數穩定性
    parameter_stability: Dict[str, float]
    most_frequent_params: Dict[str, Any]

    # 每個時期結果
    period_results: List[Dict[str, Any]]

    # 執行統計
    total_execution_time: float
    successful_optimizations: int
    failed_optimizations: int

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'analysis_config': {
                'strategy': self.strategy,
                'total_periods': self.total_periods,
                'window_size': self.window_size,
                'step_size': self.step_size,
                'test_size': self.test_size
            },
            'out_of_sample_performance': {
                'total_return': round(self.out_of_sample_return * 100, 2),
                'sharpe_ratio': round(self.out_of_sample_sharpe, 3),
                'volatility': round(self.out_of_sample_volatility * 100, 2),
                'max_drawdown': round(self.out_of_sample_max_dd * 100, 2)
            },
            'statistical_analysis': {
                'mean_return': round(self.mean_return * 100, 2),
                'std_return': round(self.std_return * 100, 2),
                'mean_sharpe': round(self.mean_sharpe, 3),
                'std_sharpe': round(self.std_sharpe, 3),
                'positive_periods': self.positive_periods,
                'positive_periods_ratio': round(self.positive_periods_ratio, 3)
            },
            'parameter_analysis': {
                'parameter_stability': self.parameter_stability,
                'most_frequent_parameters': self.most_frequent_params
            },
            'execution_stats': {
                'total_execution_time': round(self.total_execution_time, 3),
                'successful_optimizations': self.successful_optimizations,
                'failed_optimizations': self.failed_optimizations,
                'success_rate': round(self.successful_optimizations / (self.successful_optimizations + self.failed_optimizations) if (self.successful_optimizations + self.failed_optimizations) > 0 else 0, 3)
            },
            'period_details': self.period_results
        }

class WalkForwardAnalyzer:
    """
    走前分析器

    Features:
    - 滑動窗口優化
    - 樣本外測試
    - 參數穩定性分析
    - 統計顯著性測試
    - 性能評估
    """

    def __init__(self, config: Optional[WalkForwardConfig] = None):
        """初始化走前分析器"""
        self.config = config or WalkForwardConfig()

        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required for Walk Forward Analysis")

        logger.info("Walk Forward Analyzer initialized")

    def run_walk_forward_analysis(
        self,
        data: pd.DataFrame,
        strategy: Optional[str] = None,
        param_ranges: Optional[Dict[str, Any]] = None
    ) -> WalkForwardResult:
        """
        執行走前分析

        Args:
            data: OHLCV數據
            strategy: 策略名稱 (覆蓋配置)
            param_ranges: 參數範圍 (覆蓋配置)

        Returns:
            WalkForwardResult: 走前分析結果
        """
        start_time = time.time()

        try:
            logger.info(f"Starting walk-forward analysis on {len(data)} data points")

            # 使用提供參數或配置默認值
            strategy_name = strategy or self.config.strategy
            param_dict = param_ranges or self.config.param_ranges

            # 數據驗證
            if len(data) < self.config.window_size + self.config.test_size:
                raise ValueError(f"Insufficient data: {len(data)} < {self.config.window_size + self.config.test_size}")

            # 生成分析窗口
            windows = self._generate_analysis_windows(data)

            logger.info(f"Generated {len(windows)} analysis windows")

            # 執行每個窗口的分析
            period_results = []
            successful_count = 0
            failed_count = 0

            for i, window in enumerate(windows):
                try:
                    logger.info(f"Processing window {i+1}/{len(windows)}")

                    # 優化參數
                    optimal_params, optimization_results = self._optimize_parameters(
                        window['train_data'],
                        strategy_name,
                        param_dict
                    )

                    # 測試階段
                    test_result = self._test_strategy(
                        window['test_data'],
                        strategy_name,
                        optimal_params
                    )

                    # 記錄結果
                    period_result = {
                        'period': i + 1,
                        'train_start': window['train_data'].index[0],
                        'train_end': window['train_data'].index[-1],
                        'test_start': window['test_data'].index[0],
                        'test_end': window['test_data'].index[-1],
                        'optimal_params': optimal_params,
                        'test_return': test_result['total_return'],
                        'test_sharpe': test_result['sharpe_ratio'],
                        'test_drawdown': test_result['max_drawdown'],
                        'optimization_results': optimization_results
                    }

                    period_results.append(period_result)
                    successful_count += 1

                except Exception as e:
                    logger.warning(f"Failed to process window {i+1}: {e}")
                    failed_count += 1
                    continue

            # 計算整體統計
            overall_stats = self._calculate_overall_statistics(period_results)

            # 參數穩定性分析
            param_stability, most_frequent_params = self._analyze_parameter_stability(period_results)

            # 創建結果
            result = WalkForwardResult(
                strategy=strategy_name,
                total_periods=len(period_results),
                window_size=self.config.window_size,
                step_size=self.config.step_size,
                test_size=self.config.test_size,
                out_of_sample_return=overall_stats['mean_return'],
                out_of_sample_sharpe=overall_stats['mean_sharpe'],
                out_of_sample_volatility=overall_stats['mean_volatility'],
                out_of_sample_max_dd=overall_stats['mean_max_dd'],
                mean_return=overall_stats['mean_return'],
                std_return=overall_stats['std_return'],
                mean_sharpe=overall_stats['mean_sharpe'],
                std_sharpe=overall_stats['std_sharpe'],
                positive_periods=overall_stats['positive_periods'],
                positive_periods_ratio=overall_stats['positive_ratio'],
                parameter_stability=param_stability,
                most_frequent_params=most_frequent_params,
                period_results=period_results,
                total_execution_time=time.time() - start_time,
                successful_optimizations=successful_count,
                failed_optimizations=failed_count
            )

            logger.info(f"Walk-forward analysis completed in {result.total_execution_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"Walk-forward analysis failed: {e}")
            raise

    def _generate_analysis_windows(self, data: pd.DataFrame) -> List[Dict[str, pd.DataFrame]]:
        """生成分析窗口"""
        windows = []
        total_data_points = len(data)

        start_idx = 0
        window_num = 1

        while True:
            # 計算窗口邊界
            train_start = start_idx
            train_end = start_idx + self.config.window_size - 1

            if train_end >= total_data_points:
                break

            test_start = train_end + 1
            test_end = test_start + self.config.test_size - 1

            if test_end >= total_data_points:
                break

            # 提取數據
            train_data = data.iloc[train_start:train_end + 1]
            test_data = data.iloc[test_start:test_end + 1]

            windows.append({
                'window_num': window_num,
                'train_data': train_data,
                'test_data': test_data
            })

            # 移動到下一個窗口
            start_idx += self.config.step_size
            window_num += 1

        return windows

    def _optimize_parameters(
        self,
        train_data: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """在訓練數據上優化參數"""
        # 生成參數組合
        param_combinations = self._generate_parameter_combinations(param_ranges)

        if len(param_combinations) > self.config.max_combinations:
            # 隨機選擇組合
            import random
            random.shuffle(param_combinations)
            param_combinations = param_combinations[:self.config.max_combinations]

        logger.info(f"Testing {len(param_combinations)} parameter combinations")

        best_score = float('-inf')
        best_params = None
        all_scores = []

        for params in param_combinations:
            try:
                # 執行回測
                result = self._backtest_strategy(train_data, strategy, params)

                # 獲取優化指標
                if self.config.optimization_metric == 'sharpe_ratio':
                    score = result['sharpe_ratio']
                elif self.config.optimization_metric == 'total_return':
                    score = result['total_return']
                elif self.config.optimization_metric == 'calmar_ratio':
                    score = result['calmar_ratio']
                else:
                    score = result['sharpe_ratio']  # 默認

                if score > best_score:
                    best_score = score
                    best_params = params

                all_scores.append(score)

            except Exception as e:
                logger.warning(f"Failed to test parameters {params}: {e}")
                all_scores.append(0.0)
                continue

        optimization_stats = {
            'total_combinations': len(param_combinations),
            'best_score': best_score,
            'best_params': best_params,
            'mean_score': np.mean(all_scores),
            'std_score': np.std(all_scores),
            'successful_tests': len([s for s in all_scores if s > 0])
        }

        return best_params, optimization_stats

    def _test_strategy(
        self,
        test_data: pd.DataFrame,
        strategy: str,
        params: Dict[str, Any]
    ) -> Dict[str, float]:
        """在測試數據上測試策略"""
        result = self._backtest_strategy(test_data, strategy, params)

        return {
            'total_return': result['total_return'],
            'sharpe_ratio': result['sharpe_ratio'],
            'max_drawdown': result['max_drawdown'],
            'calmar_ratio': result['calmar_ratio'],
            'total_trades': result['total_trades']
        }

    def _backtest_strategy(
        self,
        data: pd.DataFrame,
        strategy: str,
        params: Dict[str, Any]
    ) -> Dict[str, float]:
        """回測策略的通用方法"""
        try:
            # 根據策略生成信號
            signals = self._generate_signals(data, strategy, params)

            # 創建投資組合
            portfolio = vbt.Portfolio.from_signals(
                close=data['close'],
                entries=signals['entries'],
                exits=signals['exits'],
                init_cash=self.config.initial_cash,
                fees=self.config.fees,
                slippage=self.config.slippage
            )

            # 計算指標
            total_return = portfolio.total_return()
            sharpe_ratio = portfolio.sharpe_ratio()
            max_drawdown = portfolio.max_drawdown()
            total_trades = len(portfolio.trades.records_readable) if len(portfolio.trades) > 0 else 0

            # Calmar比率
            calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

            return {
                'total_return': float(total_return),
                'sharpe_ratio': float(sharpe_ratio),
                'max_drawdown': float(max_drawdown),
                'calmar_ratio': float(calmar_ratio),
                'total_trades': total_trades
            }

        except Exception as e:
            logger.error(f"Backtest failed for {strategy}: {e}")
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'calmar_ratio': 0.0,
                'total_trades': 0
            }

    def _generate_signals(
        self,
        data: pd.DataFrame,
        strategy: str,
        params: Dict[str, Any]
    ) -> pd.DataFrame:
        """根據策略生成信號"""
        if strategy == "RSI_MEAN_REVERSION":
            return self._rsi_signals(data, params)
        elif strategy == "MACD_CROSSOVER":
            return self._macd_signals(data, params)
        elif strategy == "DUAL_MOVING_AVERAGE":
            return self._dual_ma_signals(data, params)
        elif strategy == "BOLLINGER_BANDS":
            return self._bollinger_signals(data, params)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _rsi_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """RSI策略信號"""
        period = params.get('period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        rsi = vbt.RSI.run(data['close'], window=period)
        rsi_values = rsi.rsi

        entries = (rsi_values < oversold) & (~(rsi_values.shift(1) < oversold))
        exits = (rsi_values > overbought) & (~(rsi_values.shift(1) > overbought))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _macd_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """MACD策略信號"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)

        macd = vbt.MACD.run(data['close'], fast_window=fast, slow_window=slow, signal_window=signal)

        entries = (macd.macd > macd.signal) & (~(macd.macd.shift(1) > macd.signal.shift(1)))
        exits = (macd.macd < macd.signal) & (~(macd.macd.shift(1) < macd.signal.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _dual_ma_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """雙移動平均策略信號"""
        short_period = params.get('short_period', 20)
        long_period = params.get('long_period', 50)

        short_ma = data['close'].rolling(short_period).mean()
        long_ma = data['close'].rolling(long_period).mean()

        entries = (short_ma > long_ma) & (~(short_ma.shift(1) > long_ma.shift(1)))
        exits = (short_ma < long_ma) & (~(short_ma.shift(1) < long_ma.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _bollinger_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """布林帶策略信號"""
        period = params.get('period', 20)

        bb = vbt.BBANDS.run(data['close'], window=period)

        entries = (data['close'] <= bb.lower) & (~(data['close'].shift(1) <= bb.lower.shift(1)))
        exits = (data['close'] >= bb.upper) & (~(data['close'].shift(1) >= bb.upper.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _generate_parameter_combinations(
        self,
        param_ranges: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成參數組合"""
        import itertools

        # 轉換所有參數為列表
        param_lists = {}
        for key, value in param_ranges.items():
            if isinstance(value, range):
                param_lists[key] = list(value)
            else:
                param_lists[key] = value

        # 生成所有組合
        keys = list(param_lists.keys())
        values = list(param_lists.values())
        combinations = list(itertools.product(*values))

        # 轉換為字典格式
        param_combinations = [
            dict(zip(keys, combo)) for combo in combinations
        ]

        return param_combinations

    def _calculate_overall_statistics(self, period_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算整體統計"""
        if not period_results:
            return {
                'mean_return': 0.0,
                'std_return': 0.0,
                'mean_sharpe': 0.0,
                'std_sharpe': 0.0,
                'positive_periods': 0,
                'positive_ratio': 0.0,
                'mean_max_dd': 0.0,
                'mean_volatility': 0.0
            }

        returns = [result['test_return'] for result in period_results]
        sharpes = [result['test_sharpe'] for result in period_results]
        drawdowns = [result['test_drawdown'] for result in period_results]

        positive_periods = sum(1 for r in returns if r > 0)

        return {
            'mean_return': np.mean(returns),
            'std_return': np.std(returns),
            'mean_sharpe': np.mean(sharpes),
            'std_sharpe': np.std(sharpes),
            'positive_periods': positive_periods,
            'positive_ratio': positive_periods / len(period_results),
            'mean_max_dd': np.mean(drawdowns),
            'mean_volatility': np.std(returns) * np.sqrt(252)  # 年化波動率
        }

    def _analyze_parameter_stability(
        self,
        period_results: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """分析參數穩定性"""
        if not period_results:
            return {}, {}

        # 收集每個參數的所有值
        param_values = {}
        for result in period_results:
            optimal_params = result['optimal_params']
            for param, value in optimal_params.items():
                if param not in param_values:
                    param_values[param] = []
                param_values[param].append(value)

        # 計算穩定性 (最頻繁值出現的比例)
        stability = {}
        most_frequent = {}

        for param, values in param_values.items():
            from collections import Counter
            counter = Counter(values)
            most_common_val, most_common_count = counter.most_common(1)[0]
            stability[param] = most_common_count / len(values)
            most_frequent[param] = most_common_val

        return stability, most_frequent

# 便利函數
def run_walk_forward_analysis(
    data: pd.DataFrame,
    strategy: str = "RSI_MEAN_REVERSION",
    param_ranges: Optional[Dict[str, Any]] = None,
    window_size: int = 252,
    step_size: int = 63
) -> WalkForwardResult:
    """便利函數：執行走前分析"""
    config = WalkForwardConfig(
        strategy=strategy,
        param_ranges=param_ranges or {},
        window_size=window_size,
        step_size=step_size
    )
    analyzer = WalkForwardAnalyzer(config)
    return analyzer.run_walk_forward_analysis(data)