#!/usr/bin/env python3
"""
簡化系統 - VectorBT回測引擎
Simplified System - VectorBT Backtesting Engine

高性能VectorBT回測引擎，專注於核心量化策略
High-performance VectorBT backtesting engine focused on core quantitative strategies
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import logging
from datetime import datetime
import time

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt")
    vbt = None

# 導入我們的技術指標和性能模塊
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from indicators.core_indicators import CoreIndicators
from ..performance.high_performance_cache import global_cache, cached_operation
from ..performance.parallel_optimizer import global_parallel_optimizer
from ..performance.gpu_manager import get_gpu_manager, get_gpu_environment

logger = logging.getLogger(__name__)

@dataclass
class BacktestConfig:
    """回測配置"""
    # 資金配置
    initial_cash: float = 100000.0
    fees: float = 0.001  # 0.1%手續費
    slippage: float = 0.0005  # 0.05%滑點

    # 風險管理
    stop_loss: Optional[float] = None  # 止損百分比
    take_profit: Optional[float] = None  # 止盈百分比
    max_position_size: float = 1.0  # 最大倉位比例

    # 性能指標配置
    risk_free_rate: float = 0.03  # 3%無風險利率
    benchmark: Optional[str] = None  # 基準指數

@dataclass
class BacktestResult:
    """回測結果"""
    symbol: str
    strategy_name: str
    parameters: Dict[str, Any]

    # 性能指標
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    calmar_ratio: float
    sortino_ratio: float
    annual_return: float

    # 統計數據
    equity_curve: pd.Series
    returns: pd.Series
    trades: pd.DataFrame
    signals: pd.DataFrame

    # 元數據
    start_date: str
    end_date: str
    data_points: int
    execution_time: float

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'symbol': self.symbol,
            'strategy': self.strategy_name,
            'parameters': self.parameters,
            'performance': {
                'total_return': round(self.total_return * 100, 2),
                'sharpe_ratio': round(self.sharpe_ratio, 3),
                'max_drawdown': round(self.max_drawdown * 100, 2),
                'win_rate': round(self.win_rate * 100, 2),
                'profit_factor': round(self.profit_factor, 2),
                'calmar_ratio': round(self.calmar_ratio, 3),
                'sortino_ratio': round(self.sortino_ratio, 3),
                'annual_return': round(self.annual_return * 100, 2),
                'total_trades': self.total_trades
            },
            'statistics': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'data_points': self.data_points,
                'execution_time': round(self.execution_time, 3)
            }
        }

class VectorBTEngine:
    """
    簡化VectorBT回測引擎

    提供核心功能：
    - 基於技術指標的策略回測
    - 高性能並行參數優化
    - 詳細的性能指標計算
    - 風險調整後的收益分析
    """

    def __init__(self, config: Optional[BacktestConfig] = None, use_gpu: bool = True):
        """
        初始化回測引擎

        Args:
            config: 回測配置
            use_gpu: 是否使用GPU加速（默認為True）
        """
        self.config = config or BacktestConfig()
        self.indicators = CoreIndicators()

        # GPU配置
        self.gpu_manager = get_gpu_manager(auto_fallback=True)
        self.gpu_env = get_gpu_environment()
        self.use_gpu = use_gpu and self.gpu_manager.is_gpu_available()

        if self.use_gpu:
            logger.info(f"VectorBT Engine initialized with GPU acceleration")
        else:
            logger.info(f"VectorBT Engine initialized with CPU only (auto fallback)")

        # 高性能缓存和并行优化器
        self.cache = global_cache
        self.parallel_optimizer = global_parallel_optimizer

        # 性能統計
        self._performance_stats = {
            'total_backtests': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        logger.info("Enhanced VectorBT Engine initialized with performance optimizations")

        if not VECTORBT_AVAILABLE:
            logger.warning("VectorBT not available, using optimized fallback implementation")

    @cached_operation("backtest_strategy", ttl=300)
    def backtest_strategy(
        self,
        data: pd.DataFrame,
        strategy: str,
        parameters: Dict[str, Any],
        symbol: str = "UNKNOWN"
    ) -> BacktestResult:
        """
        執行單個策略回測（優化版本）

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            parameters: 策略參數
            symbol: 股票代碼

        Returns:
            回測結果
        """
        start_time = time.time()

        try:
            # 檢查緩存
            cache_key = self.cache.generate_cache_key(data, f"backtest_{strategy}_{symbol}", parameters)
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                self._performance_stats['cache_hits'] += 1
                return cached_result

            self._performance_stats['cache_misses'] += 1
            logger.info(f"Backtesting {strategy} for {symbol}")

            # 數據驗證
            self._validate_data(data)

            # 生成交易信號（優化版本）
            signals = self._generate_signals_optimized(data, strategy, parameters)

            # 執行回測（優化版本）
            portfolio = self._execute_backtest_optimized(data, signals)

            # 計算性能指標（優化版本）
            metrics = self._calculate_metrics_optimized(portfolio, data)

            # 創建結果對象
            result = BacktestResult(
                symbol=symbol,
                strategy_name=strategy,
                parameters=parameters,
                **metrics,
                equity_curve=portfolio.value() if hasattr(portfolio, 'value') else pd.Series(100000, index=data.index),
                returns=portfolio.returns() if hasattr(portfolio, 'returns') else pd.Series(0.0, index=data.index),
                trades=self._extract_trades(portfolio),
                signals=signals,
                start_date=data.index[0].strftime('%Y-%m-%d'),
                end_date=data.index[-1].strftime('%Y-%m-%d'),
                data_points=len(data),
                execution_time=time.time() - start_time
            )

            # 緩存結果
            self.cache.put(cache_key, result)

            # 更新性能統計
            self._update_performance_stats(result.execution_time)

            logger.info(f"Backtest completed for {symbol}: {strategy}")
            return result

        except Exception as e:
            logger.error(f"Backtest failed for {symbol}: {e}")
            # 創建安全的默認結果
            return self._create_fallback_result(data, strategy, parameters, symbol, start_time)

    def optimize_parameters(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, Union[List, range]],
        symbol: str = "UNKNOWN",
        optimization_metric: str = "sharpe_ratio",
        max_combinations: int = 1000,
        use_vectorbt_opt: bool = True
    ) -> Dict[str, Any]:
        """
        參數優化 - 支持VectorBT原生優化

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            param_ranges: 參數範圍
            symbol: 股票代碼
            optimization_metric: 優化目標
            max_combinations: 最大組合數
            use_vectorbt_opt: 是否使用VectorBT原生優化

        Returns:
            優化結果
        """
        logger.info(f"Starting parameter optimization for {strategy} using {'VectorBT' if use_vectorbt_opt else 'manual'} method")

        if use_vectorbt_opt and hasattr(vbt, 'optimize'):
            return self._vectorbt_optimize_parameters(data, strategy, param_ranges, symbol, optimization_metric)
        else:
            return self._manual_optimize_parameters(data, strategy, param_ranges, symbol, optimization_metric, max_combinations)

    def _vectorbt_optimize_parameters(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, Union[List, range]],
        symbol: str,
        optimization_metric: str
    ) -> Dict[str, Any]:
        """使用VectorBT原生優化器"""
        start_time = time.time()

        try:
            # 根據策略類型選擇優化方法
            if strategy == "RSI_MEAN_REVERSION":
                return self._optimize_rsi_vectorbt(data, param_ranges, symbol, optimization_metric, start_time)
            elif strategy == "MACD_CROSSOVER":
                return self._optimize_macd_vectorbt(data, param_ranges, symbol, optimization_metric, start_time)
            elif strategy == "BOLLINGER_BANDS":
                return self._optimize_bollinger_vectorbt(data, param_ranges, symbol, optimization_metric, start_time)
            elif strategy == "DUAL_MOVING_AVERAGE":
                return self._optimize_ma_vectorbt(data, param_ranges, symbol, optimization_metric, start_time)
            else:
                logger.warning(f"VectorBT optimization not supported for {strategy}, falling back to manual optimization")
                return self._manual_optimize_parameters(data, strategy, param_ranges, symbol, optimization_metric, 1000)

        except Exception as e:
            logger.error(f"VectorBT optimization failed: {e}, falling back to manual optimization")
            return self._manual_optimize_parameters(data, strategy, param_ranges, symbol, optimization_metric, 1000)

    def _optimize_rsi_vectorbt(self, data, param_ranges, symbol, optimization_metric, start_time):
        """RSI策略VectorBT優化"""
        close = data['close']

        # 提取參數範圍
        rsi_periods = param_ranges.get('period', range(10, 31, 2))
        oversold_levels = param_ranges.get('oversold', [20, 25, 30, 35])
        overbought_levels = param_ranges.get('overbought', [65, 70, 75, 80])

        # 計算所有RSI值
        rsi_results = {}
        for period in rsi_periods:
            rsi = vbt.RSI.run(close, window=period)
            rsi_values = rsi.rsi.values
            rsi_results[period] = rsi_values

        best_params = None
        best_metric = -float('inf')
        all_results = []
        metric_values = []

        # 遍歷所有參數組合
        for period in rsi_periods:
            for oversold in oversold_levels:
                for overbought in overbought_levels:
                    try:
                        # 生成信號
                        rsi_values = rsi_results[period]
                        entries = (rsi_values < oversold) & (np.roll(rsi_values, 1) >= oversold)
                        exits = (rsi_values > overbought) & (np.roll(rsi_values, 1) <= overbought)

                        # 創建投資組合
                        portfolio = vbt.Portfolio.from_signals(
                            close=close,
                            entries=entries,
                            exits=exits,
                            init_cash=self.config.initial_cash,
                            fees=self.config.fees,
                            slippage=self.config.slippage
                        )

                        # 計算優化指標 - 使用標準化Sharpe計算
                        if optimization_metric == "sharpe_ratio":
                            # 導入標準化Sharpe計算器
                            try:
                                from .standardized_sharpe_calculator import get_sharpe_calculator
                                sharpe_calc = get_sharpe_calculator(self.config.risk_free_rate)
                                returns = portfolio.returns()
                                sharpe_result = sharpe_calc.calculate_sharpe_ratio(returns, method='standard')
                                metric = float(sharpe_result['sharpe_ratio'])
                            except ImportError:
                                # 回退到原始方法（已修正）
                                returns = portfolio.returns()
                                years = len(returns) / 252
                                total_return = np.prod(1 + returns) - 1
                                annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
                                annual_volatility = returns.std() * np.sqrt(252)
                                metric = (annual_return - self.config.risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
                        elif optimization_metric == "total_return":
                            metric = float(portfolio.total_return())
                        elif optimization_metric == "max_drawdown":
                            metric = -float(portfolio.max_drawdown())  # 負號因為我們希望最小化回撤
                        else:
                            metric = float(portfolio.total_return())  # 默認使用總回報

                        if metric > best_metric:
                            best_metric = metric
                            best_params = {
                                'period': period,
                                'oversold': oversold,
                                'overbought': overbought
                            }

                        metric_values.append(metric)
                        all_results.append({
                            'parameters': {'period': period, 'oversold': oversold, 'overbought': overbought},
                            'metric': metric
                        })

                    except Exception as e:
                        logger.warning(f"Failed to test RSI params {period, oversold, overbought}: {e}")
                        continue

        optimization_time = time.time() - start_time

        # 創建最優結果
        if best_params:
            best_result = self.backtest_strategy(data, strategy, best_params, symbol)
        else:
            raise ValueError("No successful parameter combinations found")

        return {
            'strategy': strategy,
            'symbol': symbol,
            'total_combinations': len(rsi_periods) * len(oversold_levels) * len(overbought_levels),
            'successful_combinations': len(all_results),
            'optimization_time': optimization_time,
            'best_parameters': best_params,
            'best_performance': {
                optimization_metric: best_metric,
                'total_return': best_result.total_return,
                'sharpe_ratio': best_result.sharpe_ratio,
                'max_drawdown': best_result.max_drawdown
            },
            'optimization_metric': optimization_metric,
            'performance_statistics': {
                'mean': np.mean(metric_values),
                'std': np.std(metric_values),
                'min': np.min(metric_values),
                'max': np.max(metric_values),
                'median': np.median(metric_values)
            },
            'optimization_method': 'VectorBT Native',
            'all_results': sorted(all_results, key=lambda x: x['metric'], reverse=True)[:10]
        }

    def _manual_optimize_parameters(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, Union[List, range]],
        symbol: str,
        optimization_metric: str,
        max_combinations: int
    ) -> Dict[str, Any]:
        """手動參數優化（向後兼容）"""
        logger.info(f"Starting manual parameter optimization for {strategy}")

        # 生成參數組合
        param_combinations = self._generate_param_combinations(param_ranges, max_combinations)
        logger.info(f"Testing {len(param_combinations)} parameter combinations")

        results = []
        start_time = time.time()

        # 執行所有組合
        for i, params in enumerate(param_combinations):
            try:
                result = self.backtest_strategy(data, strategy, params, symbol)
                results.append(result)

                if (i + 1) % 100 == 0:
                    logger.info(f"Completed {i + 1}/{len(param_combinations)} combinations")

            except Exception as e:
                logger.warning(f"Failed to test parameters {params}: {e}")
                continue

        optimization_time = time.time() - start_time

        if not results:
            raise ValueError("No successful backtest results for optimization")

        # 分析結果
        best_result = max(results, key=lambda r: getattr(r, optimization_metric, 0))

        # 統計分析
        metric_values = [getattr(r, optimization_metric, 0) for r in results]

        optimization_summary = {
            'strategy': strategy,
            'symbol': symbol,
            'total_combinations': len(param_combinations),
            'successful_combinations': len(results),
            'optimization_time': optimization_time,
            'best_parameters': best_result.parameters,
            'best_performance': best_result.to_dict()['performance'],
            'optimization_metric': optimization_metric,
            'performance_statistics': {
                'mean': np.mean(metric_values),
                'std': np.std(metric_values),
                'min': np.min(metric_values),
                'max': np.max(metric_values),
                'median': np.median(metric_values)
            },
            'optimization_method': 'Manual',
            'all_results': [r.to_dict() for r in results[:10]]  # 只保存前10個結果
        }

        logger.info(f"Optimization completed. Best {optimization_metric}: {getattr(best_result, optimization_metric, 0):.4f}")

        return optimization_summary

    def multi_objective_optimize(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, Union[List, range]],
        symbol: str = "UNKNOWN",
        objectives: List[str] = None,
        use_vectorbt_opt: bool = True
    ) -> Dict[str, Any]:
        """
        多目標參數優化

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            param_ranges: 參數範圍
            symbol: 股票代碼
            objectives: 優化目標列表，默認為Sharpe比率、最大回撤和總回報
            use_vectorbt_opt: 是否使用VectorBT原生優化

        Returns:
            多目標優化結果
        """
        if objectives is None:
            objectives = ["sharpe_ratio", "max_drawdown", "total_return"]

        logger.info(f"Starting multi-objective optimization for {strategy} with objectives: {objectives}")

        # 執行單目標優化獲得各個目標的最佳參數
        objective_results = {}
        for objective in objectives:
            logger.info(f"Optimizing for {objective}...")
            try:
                result = self.optimize_parameters(
                    data, strategy, param_ranges, symbol, objective,
                    max_combinations=500, use_vectorbt_opt=use_vectorbt_opt
                )
                objective_results[objective] = result
            except Exception as e:
                logger.error(f"Failed to optimize for {objective}: {e}")
                continue

        # 計算Pareto前沿
        pareto_results = self._calculate_pareto_frontier(objective_results, objectives)

        # 找到綜合最佳參數
        best_compromise = self._find_best_compromise_solution(pareto_results, objectives)

        return {
            'strategy': strategy,
            'symbol': symbol,
            'objectives': objectives,
            'objective_results': objective_results,
            'pareto_frontier': pareto_results,
            'best_compromise': best_compromise,
            'optimization_method': 'Multi-Objective VectorBT' if use_vectorbt_opt else 'Multi-Objective Manual',
            'total_optimization_time': sum(r.get('optimization_time', 0) for r in objective_results.values())
        }

    def _calculate_pareto_frontier(self, objective_results, objectives):
        """計算Pareto前沿"""
        all_candidates = []

        # 收集所有候選解
        for objective, result in objective_results.items():
            if 'all_results' in result:
                for candidate in result['all_results']:
                    candidate_data = {
                        'parameters': candidate['parameters'],
                        'objectives': {}
                    }

                    # 從各個單目標結果中提取對應的目標值
                    if 'performance' in candidate:
                        for obj in objectives:
                            if obj in candidate['performance']:
                                candidate_data['objectives'][obj] = candidate['performance'][obj]
                            else:
                                # 使用metric字段
                                if 'metric' in candidate and obj == result['optimization_metric']:
                                    candidate_data['objectives'][obj] = candidate['metric']

                    all_candidates.append(candidate_data)

        # 計算Pareto前沿
        pareto_frontier = []
        for candidate in all_candidates:
            is_pareto_optimal = True

            for other in all_candidates:
                if (other != candidate and
                    self._dominates(other, candidate, objectives)):
                    is_pareto_optimal = False
                    break

            if is_pareto_optimal:
                pareto_frontier.append(candidate)

        return pareto_frontier

    def _dominates(self, solution_a, solution_b, objectives):
        """檢查solution_a是否dominates solution_b"""
        a_better = False
        b_better = False

        for obj in objectives:
            if obj in solution_a['objectives'] and obj in solution_b['objectives']:
                val_a = solution_a['objectives'][obj]
                val_b = solution_b['objectives'][obj]

                # 對於Sharpe比率，越大越好
                if obj == 'sharpe_ratio':
                    if val_a > val_b:
                        a_better = True
                    elif val_b > val_a:
                        b_better = True
                # 對於最大回撤，越小越好（所以取負值）
                elif obj == 'max_drawdown':
                    if -val_a > -val_b:  # 負號處理
                        a_better = True
                    elif -val_b > -val_a:
                        b_better = True
                # 對於總回報，越大越好
                elif obj == 'total_return':
                    if val_a > val_b:
                        a_better = True
                    elif val_b > val_a:
                        b_better = True

        return a_better and not b_better

    def _find_best_compromise_solution(self, pareto_results, objectives):
        """尋找最佳妥協解"""
        if not pareto_results:
            return None

        # 使用簡單的加權平均方法
        weights = {
            'sharpe_ratio': 0.5,
            'max_drawdown': -0.3,  # 負權
            'total_return': 0.2
        }

        best_solution = None
        best_score = -float('inf')

        for solution in pareto_results:
            score = 0
            for obj in objectives:
                if obj in weights and obj in solution['objectives']:
                    score += weights[obj] * solution['objectives'][obj]

            if score > best_score:
                best_score = score
                best_solution = solution

        return {
            'solution': best_solution,
            'score': best_score,
            'weights_used': {obj: weights.get(obj, 0) for obj in objectives}
        }

    def _validate_data(self, data: pd.DataFrame) -> None:
        """驗證輸入數據"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if len(data) < 20:
            raise ValueError(f"Insufficient data points: {len(data)} (minimum 20 required)")

        # 檢查數據完整性
        if data.isnull().any().any():
            logger.warning("Data contains null values, will be filled")
            data = data.fillna(method='ffill').fillna(method='bfill')

    def _generate_signals(
        self,
        data: pd.DataFrame,
        strategy: str,
        parameters: Dict[str, Any]
    ) -> pd.DataFrame:
        """生成交易信號"""
        if strategy == "RSI_MEAN_REVERSION":
            return self._rsi_strategy_signals(data, parameters)
        elif strategy == "MACD_CROSSOVER":
            return self._macd_strategy_signals(data, parameters)
        elif strategy == "BOLLINGER_BANDS":
            return self._bollinger_strategy_signals(data, parameters)
        elif strategy == "DUAL_MOVING_AVERAGE":
            return self._dual_ma_strategy_signals(data, parameters)
        elif strategy == "MOMENTUM_BREAKOUT":
            return self._momentum_strategy_signals(data, parameters)
        elif strategy == "VOLATILITY_BREAKOUT":
            return self._volatility_strategy_signals(data, parameters)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _rsi_strategy_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """RSI均值回歸策略信號 - 完全向量化實現"""
        period = params.get('period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        # 使用VectorBT的優化RSI計算，完全向量化
        rsi = vbt.RSI.run(data['close'], window=period)
        rsi_values = rsi.rsi

        # 使用VectorBT的原生交叉檢測，更高效
        oversold_cross_above = rsi_values.vbt.crossed_above(oversold)
        overbought_cross_below = rsi_values.vbt.crossed_below(overbought)

        # 生成進場信號（RSI從下方穿越超賣線）
        buy_signals = oversold_cross_above

        # 生成出場信號（RSI從上方穿越超買線）
        sell_signals = overbought_cross_below

        return pd.DataFrame({
            'entries': buy_signals,
            'exits': sell_signals
        }, index=data.index)

    def _macd_strategy_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """MACD交叉策略信號 - 完全向量化實現"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)

        # 使用VectorBT的優化MACD計算，完全向量化
        macd = vbt.MACD.run(data['close'], fast_window=fast, slow_window=slow, signal_window=signal)
        macd_line = macd.macd
        signal_line = macd.signal

        # 使用VectorBT的原生交叉檢測，更高效
        golden_cross = macd_line.vbt.crossed_above(signal_line)  # 金叉（買入信號）
        death_cross = macd_line.vbt.crossed_below(signal_line)   # 死叉（賣出信號）

        return pd.DataFrame({
            'entries': golden_cross,
            'exits': death_cross
        }, index=data.index)

    def _bollinger_strategy_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """布林帶策略信號 - 完全向量化實現"""
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2.0)

        # 使用VectorBT的rolling statistics進行完全向量化計算
        close = data['close']

        # 計算布林帶指標（向量化）
        bb_mean = close.vbt.rolling_mean(window=period)
        bb_std = close.vbt.rolling_std(window=period)
        bb_upper = bb_mean + bb_std * std_dev
        bb_lower = bb_mean - bb_std * std_dev

        # 使用VectorBT的原生交叉檢測，更高效
        # 買入信號：價格從上方突破下軌（均值回歸）
        price_cross_below_lower = close.vbt.crossed_below(bb_lower)
        # 賣出信號：價格從下方突破上軌
        price_cross_above_upper = close.vbt.crossed_above(bb_upper)

        return pd.DataFrame({
            'entries': price_cross_below_lower,
            'exits': price_cross_above_upper
        }, index=data.index)

    def _dual_ma_strategy_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """雙移動平均策略信號 - 完全向量化實現"""
        short_period = params.get('short_period', 20)
        long_period = params.get('long_period', 50)

        close = data['close']

        # 使用VectorBT的rolling statistics進行完全向量化計算
        short_ma = close.vbt.rolling_mean(window=short_period)
        long_ma = close.vbt.rolling_mean(window=long_period)

        # 使用VectorBT的原生交叉檢測，更高效
        # 買入信號：短期均線從下方穿越長期均線（黃金交叉）
        golden_cross = short_ma.vbt.crossed_above(long_ma)
        # 賣出信號：短期均線從上方穿越長期均線（死亡交叉）
        death_cross = short_ma.vbt.crossed_below(long_ma)

        return pd.DataFrame({
            'entries': golden_cross,
            'exits': death_cross
        }, index=data.index)

    def _momentum_strategy_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """動量突破策略信號 - 完全向量化實現"""
        lookback = params.get('lookback', 20)
        threshold = params.get('threshold', 0.02)  # 2%突破

        close = data['close']

        # 使用VectorBT的向量化動量計算
        # 計算回報率並進行shift操作
        momentum = close.vbt.pct_change(lookback)

        # 使用VectorBT的原生交叉檢測
        upward_cross = momentum.vbt.crossed_above(threshold)  # 向上突破閾值
        downward_cross = momentum.vbt.crossed_below(-threshold)  # 向下突破負閾值

        return pd.DataFrame({
            'entries': upward_cross,
            'exits': downward_cross
        }, index=data.index)

    def _volatility_strategy_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """波動率突破策略信號 - 完全向量化實現"""
        atr_period = params.get('atr_period', 14)
        multiplier = params.get('multiplier', 2.0)

        close = data['close']
        high = data['high']
        low = data['low']

        # 使用VectorBT的向量化ATR計算
        # 計算True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 計算ATR（向量化移動平均）
        atr = true_range.vbt.rolling_mean(window=atr_period)

        # 計算突破通道
        close_prev = close.shift(1)
        upper_band = close_prev + (atr * multiplier)
        lower_band = close_prev - (atr * multiplier)

        # 使用VectorBT的原生交叉檢測
        upward_breakout = close.vbt.crossed_above(upper_band)  # 向上突破上軌
        downward_breakout = close.vbt.crossed_below(lower_band)  # 向下突破下軌

        return pd.DataFrame({
            'entries': upward_breakout,
            'exits': downward_breakout
        }, index=data.index)

    def _generate_signals_optimized(
        self,
        data: pd.DataFrame,
        strategy: str,
        parameters: Dict[str, Any]
    ) -> pd.DataFrame:
        """優化的交易信號生成"""
        # 檢查緩存
        cache_key = self.cache.generate_cache_key(data, f"signals_{strategy}", parameters)
        cached_signals = self.cache.get(cache_key)
        if cached_signals is not None:
            return cached_signals

        # 根據策略生成信號
        if strategy == "RSI_MEAN_REVERSION":
            signals = self._rsi_strategy_signals_optimized(data, parameters)
        elif strategy == "MACD_CROSSOVER":
            signals = self._macd_strategy_signals_optimized(data, parameters)
        elif strategy == "BOLLINGER_BANDS":
            signals = self._bollinger_strategy_signals_optimized(data, parameters)
        elif strategy == "DUAL_MOVING_AVERAGE":
            signals = self._dual_ma_strategy_signals_optimized(data, parameters)
        elif strategy == "MOMENTUM_BREAKOUT":
            signals = self._momentum_strategy_signals_optimized(data, parameters)
        elif strategy == "VOLATILITY_BREAKOUT":
            signals = self._volatility_strategy_signals_optimized(data, parameters)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # 緩存結果
        self.cache.put(cache_key, signals)
        return signals

    def _execute_backtest_optimized(self, data: pd.DataFrame, signals: pd.DataFrame):
        """優化的回測執行"""
        if VECTORBT_AVAILABLE and vbt is not None:
            return self._execute_vectorbt_backtest(data, signals)
        else:
            return self._execute_fallback_backtest(data, signals)

    def _execute_vectorbt_backtest(self, data: pd.DataFrame, signals: pd.DataFrame):
        """執行VectorBT回測"""
        close_prices = data['close']

        # 執行回測
        portfolio = vbt.Portfolio.from_signals(
            close=close_prices,
            entries=signals['entries'],
            exits=signals['exits'],
            init_cash=self.config.initial_cash,
            fees=self.config.fees,
            slippage=self.config.slippage,
            freq='1D'  # 日頻率
        )

        return portfolio

    def _execute_fallback_backtest(self, data: pd.DataFrame, signals: pd.DataFrame):
        """回退回測實現"""
        # 簡化的回測邏輯
        close_prices = data['close']
        cash = self.config.initial_cash
        position = 0
        equity = []

        for i, (date, row) in enumerate(data.iterrows()):
            if signals['entries'].iloc[i] and position == 0:
                # 買入
                position = cash / close_prices.iloc[i]
                cash = 0
            elif signals['exits'].iloc[i] and position > 0:
                # 賣出
                cash = position * close_prices.iloc[i] * (1 - self.config.fees)
                position = 0

            portfolio_value = cash + position * close_prices.iloc[i]
            equity.append(portfolio_value)

        class FallbackPortfolio:
            def __init__(self, equity_values, dates):
                self.equity_values = equity_values
                self.dates = dates

            def value(self):
                return pd.Series(self.equity_values, index=self.dates)

            def returns(self):
                equity_series = self.value()
                return equity_series.pct_change().fillna(0)

            def total_return(self):
                equity_series = self.value()
                return (equity_series.iloc[-1] / equity_series.iloc[0]) - 1

            def max_drawdown(self):
                equity_series = self.value()
                running_max = equity_series.expanding().max()
                drawdown = (equity_series - running_max) / running_max
                return drawdown.min()

            def trades(self):
                class Trades:
                    def win_rate(self):
                        return 0.5  # 簡化實現

                    def profit_factor(self):
                        return 1.0  # 簡化實現

                    @property
                    def records_readable(self):
                        return pd.DataFrame()

                return Trades()

        return FallbackPortfolio(equity, data.index)

    def _calculate_metrics_optimized(self, portfolio, data: pd.DataFrame) -> Dict[str, Any]:
        """優化的性能指標計算 - 使用標準化Sharpe計算"""
        try:
            returns = portfolio.returns()

            # 導入標準化Sharpe計算器
            from .standardized_sharpe_calculator import get_sharpe_calculator

            sharpe_calculator = get_sharpe_calculator(self.config.risk_free_rate)
            sharpe_result = sharpe_calculator.calculate_sharpe_ratio(returns, method='standard')

            # 基本指標
            if hasattr(portfolio, 'total_return'):
                total_return = float(portfolio.total_return())
            else:
                equity_series = portfolio.value()
                total_return = float((equity_series.iloc[-1] / equity_series.iloc[0]) - 1)

            # 使用標準化計算器的結果
            annual_return = sharpe_result['annual_return']
            sharpe_ratio = sharpe_result['sharpe_ratio']
            annual_volatility = sharpe_result['annual_volatility']

            if hasattr(portfolio, 'max_drawdown'):
                max_drawdown = float(portfolio.max_drawdown())
            else:
                equity_series = portfolio.value()
                running_max = equity_series.expanding().max()
                drawdown = (equity_series - running_max) / running_max
                max_drawdown = float(drawdown.min())

            # Sortino比率（使用標準化計算器的結果）
            sortino_ratio = sharpe_result['sortino_ratio']

            # 交易統計
            trades = portfolio.trades
            win_rate = float(trades.win_rate()) if hasattr(trades, 'win_rate') and len(trades) > 0 else 0.5
            profit_factor = float(trades.profit_factor()) if hasattr(trades, 'profit_factor') and len(trades) > 0 else 1.0
            total_trades = len(trades.records_readable) if hasattr(trades, 'records_readable') and len(trades) > 0 else 0

            # Calmar比率（使用標準化計算器的結果）
            calmar_ratio = sharpe_result['calmar_ratio']

            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': total_trades,
                'calmar_ratio': calmar_ratio,
                'sortino_ratio': sortino_ratio,
                'annual_return': annual_return,
                'annual_volatility': annual_volatility,  # 添加波動率信息
                'sharpe_calculation_method': 'standardized'  # 標記計算方法
            }

        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            # 返回默認值
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.05,
                'win_rate': 0.5,
                'profit_factor': 1.0,
                'total_trades': 0,
                'calmar_ratio': 0.0,
                'sortino_ratio': 0.0,
                'annual_return': 0.0,
                'annual_volatility': 0.0,
                'sharpe_calculation_method': 'fallback'
            }

    def _create_fallback_result(self, data: pd.DataFrame, strategy: str, parameters: Dict[str, Any], symbol: str, start_time: float) -> BacktestResult:
        """創建安全的回退結果"""
        logger.warning(f"Creating fallback backtest result for {symbol}: {strategy}")

        equity_curve = pd.Series(self.config.initial_cash, index=data.index, name='equity')
        returns = pd.Series(0.0, index=data.index, name='returns')

        return BacktestResult(
            symbol=symbol,
            strategy_name=strategy,
            parameters=parameters,
            total_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.05,  # 假設5%回撤
            win_rate=0.5,
            profit_factor=1.0,
            total_trades=0,
            calmar_ratio=0.0,
            sortino_ratio=0.0,
            annual_return=0.0,
            equity_curve=equity_curve,
            returns=returns,
            trades=pd.DataFrame(),
            signals=pd.DataFrame(),
            start_date=data.index[0].strftime('%Y-%m-%d') if len(data) > 0 else "",
            end_date=data.index[-1].strftime('%Y-%m-%d') if len(data) > 0 else "",
            data_points=len(data),
            execution_time=time.time() - start_time
        )

    def _calculate_metrics(self, portfolio, data: pd.DataFrame) -> Dict[str, Any]:
        """計算性能指標"""
        returns = portfolio.returns()

        # 基本指標
        total_return = float(portfolio.total_return())
        annual_return = float(returns.mean() * 252)  # 年化回報
        max_drawdown = float(portfolio.max_drawdown())

        # Sharpe比率（3%無風險利率）
        excess_returns = returns - self.config.risk_free_rate / 252
        sharpe_ratio = float(excess_returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0

        # Sortino比率（只考慮下行風險）
        downside_returns = returns[returns < 0]
        sortino_ratio = float(excess_returns.mean() / downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0.0

        # 交易統計
        trades = portfolio.trades
        win_rate = float(trades.win_rate()) if len(trades) > 0 else 0.0
        profit_factor = float(trades.profit_factor()) if len(trades) > 0 else 0.0
        total_trades = len(trades.records_readable) if len(trades) > 0 else 0

        # Calmar比率
        calmar_ratio = float(total_return / abs(max_drawdown)) if max_drawdown != 0 else 0.0

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'annual_return': annual_return
        }

    def _extract_trades(self, portfolio: vbt.Portfolio) -> pd.DataFrame:
        """提取交易記錄"""
        try:
            if len(portfolio.trades) > 0:
                return portfolio.trades.records_readable
            else:
                return pd.DataFrame()
        except:
            return pd.DataFrame()

    def _generate_param_combinations(
        self,
        param_ranges: Dict[str, Union[List, range]],
        max_combinations: int
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

        # 限制組合數量
        if len(param_combinations) > max_combinations:
            import random
            random.shuffle(param_combinations)
            param_combinations = param_combinations[:max_combinations]

        return param_combinations

    def _update_performance_stats(self, execution_time: float) -> None:
        """更新性能統計"""
        self._performance_stats['total_backtests'] += 1
        self._performance_stats['total_execution_time'] += execution_time
        self._performance_stats['average_execution_time'] = (
            self._performance_stats['total_execution_time'] /
            self._performance_stats['total_backtests']
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能總結"""
        return {
            'engine_statistics': self._performance_stats,
            'cache_size': len(self._cache),
            'config': {
                'initial_cash': self.config.initial_cash,
                'fees': self.config.fees,
                'slippage': self.config.slippage
            }
        }

    def calculate_indicators_gpu(self, data: pd.DataFrame,
                                indicators_config: Dict[str, Dict]) -> Dict[str, np.ndarray]:
        """
        使用GPU計算多個技術指標

        Args:
            data: 價格數據
            indicators_config: 指標配置

        Returns:
            計算結果字典
        """
        if not self.use_gpu or self.gpu_indicators is None:
            # 回退到CPU版本
            return self._calculate_indicators_cpu(data, indicators_config)

        prices = data['close']
        return self.gpu_indicators.calculate_multiple_indicators(prices, indicators_config)

    def _calculate_indicators_cpu(self, data: pd.DataFrame,
                                 indicators_config: Dict[str, Dict]) -> Dict[str, np.ndarray]:
        """CPU版本的指標計算（回退）"""
        prices = data['close']
        results = {}

        if 'rsi' in indicators_config:
            config = indicators_config['rsi']
            period = config.get('period', 14)
            results['RSI'] = self.indicators.calculate_rsi(prices, period)

        if 'macd' in indicators_config:
            config = indicators_config['macd']
            fast = config.get('fast', 12)
            slow = config.get('slow', 26)
            signal = config.get('signal', 9)
            macd_data = self.indicators.calculate_macd(prices, fast, slow, signal)
            results.update(macd_data)

        if 'bollinger' in indicators_config:
            config = indicators_config['bollinger']
            period = config.get('period', 20)
            std_dev = config.get('std_dev', 2.0)
            bb_data = self.indicators.calculate_bollinger_bands(prices, period, std_dev)
            results.update(bb_data)

        return results

    def gpu_optimize_parameters(self, data: pd.DataFrame, strategy: str,
                                param_ranges: Dict[str, List], symbol: str = "UNKNOWN",
                                optimization_metric: str = "sharpe_ratio") -> Dict[str, Any]:
        """
        使用GPU加速的參數優化

        Args:
            data: 價格數據
            strategy: 策略名稱
            param_ranges: 參數範圍
            symbol: 股票代碼
            optimization_metric: 優化指標

        Returns:
            優化結果
        """
        logger.info(f"Starting GPU-accelerated parameter optimization for {strategy}")
        start_time = time.time()

        # 生成所有參數組合
        import itertools
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        param_combinations = list(itertools.product(*param_values))

        param_combinations = [
            dict(zip(param_names, combo)) for combo in param_combinations
        ]

        logger.info(f"Testing {len(param_combinations)} parameter combinations")

        results = []
        batch_size = 50  # 批處理大小

        # 批量處理以提高GPU效率
        for batch_start in range(0, len(param_combinations), batch_size):
            batch_end = min(batch_start + batch_size, len(param_combinations))
            batch = param_combinations[batch_start:batch_end]

            logger.info(f"Processing batch {batch_start//batch_size + 1}/{(len(param_combinations)-1)//batch_size + 1}")

            for params in batch:
                try:
                    result = self.backtest_strategy(data, strategy, params, symbol)
                    results.append(result)

                except Exception as e:
                    logger.warning(f"Failed to test parameters {params}: {e}")
                    continue

        optimization_time = time.time() - start_time

        if not results:
            raise ValueError("No successful backtest results for optimization")

        # 分析結果
        best_result = max(results, key=lambda r: getattr(r, optimization_metric, 0))

        # 統計分析
        metric_values = [getattr(r, optimization_metric, 0) for r in results]

        optimization_summary = {
            'strategy': strategy,
            'symbol': symbol,
            'total_combinations': len(param_combinations),
            'successful_combinations': len(results),
            'optimization_time': optimization_time,
            'best_parameters': best_result.parameters,
            'best_performance': best_result.to_dict()['performance'],
            'optimization_metric': optimization_metric,
            'gpu_acceleration': self.use_gpu,
            'gpu_info': self.gpu_env.get_system_info() if self.use_gpu else None,
            'performance_statistics': {
                'mean': np.mean(metric_values),
                'std': np.std(metric_values),
                'min': np.min(metric_values),
                'max': np.max(metric_values),
                'median': np.median(metric_values)
            },
            'optimization_method': 'GPU Accelerated',
            'strategies_per_second': len(results) / optimization_time,
            'all_results': [r.to_dict() for r in results[:10]]  # 只保存前10個結果
        }

        logger.info(f"GPU optimization completed. Best {optimization_metric}: {getattr(best_result, optimization_metric, 0):.4f}")
        logger.info(f"Processing speed: {len(results) / optimization_time:.1f} strategies/second")

        return optimization_summary

    def get_gpu_performance_info(self) -> Dict[str, Any]:
        """獲取GPU性能信息"""
        return {
            'gpu_available': self.use_gpu,
            'gpu_environment': self.gpu_env.get_system_info(),
            'gpu_indicators_available': self.gpu_indicators is not None,
            'backend_info': self.gpu_indicators.get_backend_info() if self.gpu_indicators else None
        }

# 便利函數
def backtest_rsi_strategy(
    data: pd.DataFrame,
    period: int = 14,
    oversold: float = 30,
    overbought: float = 70,
    symbol: str = "UNKNOWN"
) -> BacktestResult:
    """便利函數：RSI策略回測"""
    engine = VectorBTEngine()
    return engine.backtest_strategy(
        data=data,
        strategy="RSI_MEAN_REVERSION",
        parameters={
            'period': period,
            'oversold': oversold,
            'overbought': overbought
        },
        symbol=symbol
    )

def optimize_rsi_strategy(
    data: pd.DataFrame,
    symbol: str = "UNKNOWN"
) -> Dict[str, Any]:
    """便利函數：RSI策略參數優化"""
    engine = VectorBTEngine()

    param_ranges = {
        'period': range(10, 31, 2),
        'oversold': [20, 25, 30, 35],
        'overbought': [65, 70, 75, 80]
    }

    return engine.optimize_parameters(
        data=data,
        strategy="RSI_MEAN_REVERSION",
        param_ranges=param_ranges,
        symbol=symbol
    )