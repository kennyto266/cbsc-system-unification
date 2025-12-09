#!/usr/bin/env python3
"""
增強系統 - 進階VectorBT回測引擎
Enhanced System - Advanced VectorBT Backtesting Engine

專業級VectorBT回測引擎，支持多資產、進階風險管理和投資組合優化
Professional-grade VectorBT backtesting engine with multi-asset support, advanced risk management, and portfolio optimization
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta
import time
from functools import lru_cache
import concurrent.futures
from scipy import stats, optimize
import warnings

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available. Install with: pip install vectorbt[yfinance]")

# 導入現有模塊
from .vectorbt_engine import BacktestConfig, BacktestResult, VectorBTEngine
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from indicators.core_indicators import CoreIndicators
from indicators.technical_analyzer import TechnicalAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class EnhancedBacktestConfig(BacktestConfig):
    """增強回測配置"""
    # 多資產配置
    max_positions: int = 10  # 最大持倉數量
    min_position_weight: float = 0.05  # 最小倉位權重 (5%)
    max_position_weight: float = 0.20  # 最大倉位權重 (20%)
    rebalance_freq: Optional[str] = None  # 再平衡頻率 ('M' = 月度, 'W' = 週度)

    # 高級風險管理
    var_confidence: float = 0.95  # VaR置信度
    var_method: str = "historical"  # VaR計算方法 ('historical', 'parametric')
    lookback_days: int = 252  # 風險計算回望期

    # 性能優化
    enable_parallel: bool = True  # 啟用並行處理
    max_workers: int = 4  # 最大工作線程數
    chunk_size: int = 10000  # 數據分塊大小

@dataclass
class AdvancedRiskMetrics:
    """進階風險指標"""
    var_95: float = 0.0
    var_99: float = 0.0
    expected_shortfall: float = 0.0
    calmar_ratio: float = 0.0
    sortino_ratio: float = 0.0
    information_ratio: float = 0.0
    tracking_error: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0
    max_drawdown_duration: int = 0
    recovery_time: int = 0

class EnhancedVectorBTEngine(VectorBTEngine):
    """
    增強VectorBT回測引擎

    提供進階功能：
    - 多資產投資組合回測
    - 高級風險指標計算
    - 並行參數優化
    - 走前分析框架
    - 投資組合優化
    """

    def __init__(self, config: Optional[EnhancedBacktestConfig] = None):
        """初始化增強回測引擎"""
        self.config = config or EnhancedBacktestConfig()
        self.indicators = CoreIndicators()
        self.analyzer = TechnicalAnalyzer()

        # 策略註冊表
        self._strategy_registry = {}
        self._register_strategies()

        # 緩存機制
        self._cache = {}
        self._cache_ttl = 300  # 5分鐘緩存

        # 性能統計
        self._performance_stats = {
            'total_backtests': 0,
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        logger.info("Enhanced VectorBT Engine initialized")

        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required. Install with: pip install vectorbt[yfinance]")

    def _register_strategies(self):
        """註冊所有可用策略"""
        # 基本策略 - 使用父類方法
        self._strategy_registry.update({
            'RSI_MEAN_REVERSION': self._rsi_strategy_signals,
            'MACD_CROSSOVER': self._macd_strategy_signals,
            'BOLLINGER_BANDS': self._bollinger_strategy_signals,
            'DUAL_MOVING_AVERAGE': self._dual_ma_strategy_signals,
            'MOMENTUM_BREAKOUT': self._momentum_strategy_signals,
            'VOLATILITY_BREAKOUT': self._volatility_strategy_signals,
        })

        # 進階策略
        self._strategy_registry.update({
            'ADVANCED_MEAN_REVERSION': self._advanced_mean_reversion_signals,
            'DUAL_RSI_CONFLUENCE': self._dual_rsi_confluence_signals,
            'ICHIMOKU_CLOUD': self._ichimoku_cloud_signals,
            'ADX_MOMENTUM': self._adx_momentum_signals,
            'ATR_VOLATILITY_BREAKOUT': self._atr_volatility_breakout_signals,
            'MULTI_TIMEFRAME_RSI': self._multi_timeframe_rsi_signals,
            'VIX_REVERSION': self._vix_reversion_signals,
            'PAIR_TRADING': self._pair_trading_signals,
        })

    def backtest_portfolio(
        self,
        data_dict: Dict[str, pd.DataFrame],
        strategy: str,
        parameters: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, BacktestResult]:
        """
        執行多資產投資組合回測

        Args:
            data_dict: 多資產OHLCV數據字典 {symbol: dataframe}
            strategy: 策略名稱
            parameters: 策略參數
            weights: 資產權重字典

        Returns:
            投資組合回測結果字典
        """
        start_time = time.time()

        try:
            logger.info(f"Portfolio backtesting {strategy} for {len(data_dict)} assets")

            # 驗證數據
            self._validate_portfolio_data(data_dict)

            # 生成信號
            signals_dict = {}
            for symbol, data in data_dict.items():
                signals_dict[symbol] = self._generate_signals(data, strategy, parameters)

            # 計算權重
            if weights is None:
                weights = {symbol: 1.0/len(data_dict) for symbol in data_dict.keys()}

            # 執行投資組合回測
            portfolio_results = self._execute_portfolio_backtest(
                data_dict, signals_dict, weights
            )

            # 計算進階風險指標
            for result in portfolio_results.values():
                result.advanced_risk_metrics = self._calculate_advanced_risk_metrics(
                    result.returns, self.config
                )

            # 更新性能統計
            execution_time = time.time() - start_time
            self._update_performance_stats(execution_time)

            logger.info(f"Portfolio backtest completed in {execution_time:.3f}s")
            return portfolio_results

        except Exception as e:
            logger.error(f"Portfolio backtest failed: {e}")
            raise

    def optimize_parameters_parallel(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, Union[List, range]],
        symbol: str = "UNKNOWN",
        optimization_metric: str = "sharpe_ratio",
        max_combinations: int = 1000
    ) -> Dict[str, Any]:
        """
        並行參數優化

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            param_ranges: 參數範圍
            symbol: 股票代碼
            optimization_metric: 優化目標
            max_combinations: 最大組合數

        Returns:
            優化結果
        """
        logger.info(f"Starting parallel parameter optimization for {strategy}")

        # 生成參數組合
        param_combinations = self._generate_param_combinations(param_ranges, max_combinations)
        logger.info(f"Testing {len(param_combinations)} parameter combinations")

        results = []
        start_time = time.time()

        if self.config.enable_parallel:
            # 並行處理
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []

                for params in param_combinations:
                    future = executor.submit(
                        self._backtest_single_safe, data, strategy, params, symbol
                    )
                    futures.append(future)

                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    try:
                        result = future.result()
                        if result and hasattr(result, 'sharpe_ratio'):
                            results.append(result)

                        if (i + 1) % 100 == 0:
                            logger.info(f"Completed {i + 1}/{len(futures)} combinations")

                    except Exception as e:
                        logger.warning(f"Parameter combination failed: {e}")
                        continue
        else:
            # 順序處理
            for params in param_combinations:
                try:
                    result = self._backtest_single_safe(data, strategy, params, symbol)
                    if result and hasattr(result, 'sharpe_ratio'):
                        results.append(result)

                    if (len(results) % 100 == 0):
                        logger.info(f"Completed {len(results)}/{len(param_combinations)} combinations")

                except Exception as e:
                    logger.warning(f"Parameter combination failed: {e}")
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
            'best_performance': best_result.to_dict(),
            'optimization_metric': optimization_metric,
            'performance_statistics': {
                'mean': np.mean(metric_values),
                'std': np.std(metric_values),
                'min': np.min(metric_values),
                'max': np.max(metric_values),
                'median': np.median(metric_values)
            },
            'all_results': [r.to_dict() for r in results[:10]]  # 只保存前10個結果
        }

        logger.info(f"Parallel optimization completed. Best {optimization_metric}: {getattr(best_result, optimization_metric, 0):.4f}")

        return optimization_summary

    def walk_forward_analysis(
        self,
        data: pd.DataFrame,
        strategy: str,
        param_ranges: Dict[str, Union[List, range]],
        window_size: int = 504,  # 2年
        step_size: int = 126,    # 6個月
        test_size: int = 63,     # 3個月
        symbol: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """
        走前分析

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            param_ranges: 參數範圍
            window_size: 優化窗口大小
            step_size: 步長
            test_size: 測試窗口大小
            symbol: 股票代碼

        Returns:
            走前分析結果
        """
        logger.info(f"Starting walk-forward analysis for {strategy}")

        total_periods = (len(data) - window_size - test_size) // step_size + 1
        results = []

        for i in range(total_periods):
            train_start = i * step_size
            train_end = train_start + window_size
            test_start = train_end
            test_end = test_start + test_size

            if test_end > len(data):
                break

            # 訓練集優化
            train_data = data.iloc[train_start:train_end]
            optimization_result = self.optimize_parameters_parallel(
                train_data, strategy, param_ranges, symbol
            )

            # 測試集驗證
            test_data = data.iloc[test_start:test_end]
            best_params = optimization_result['best_parameters']

            test_result = self._backtest_single_safe(
                test_data, strategy, best_params, symbol
            )

            if test_result:
                results.append({
                    'period': i + 1,
                    'train_start': train_start,
                    'train_end': train_end,
                    'test_start': test_start,
                    'test_end': test_end,
                    'optimal_params': best_params,
                    'test_performance': test_result.to_dict(),
                    'optimization_performance': optimization_result['best_performance']
                })

            logger.info(f"Completed period {i + 1}/{total_periods}")

        # 聚合結果
        if results:
            test_returns = [r['test_performance']['performance']['total_return'] for r in results]
            test_sharpes = [r['test_performance']['performance']['sharpe_ratio'] for r in results]

            walk_forward_summary = {
                'strategy': strategy,
                'symbol': symbol,
                'total_periods': len(results),
                'window_size': window_size,
                'step_size': step_size,
                'test_size': test_size,
                'out_of_sample_performance': {
                    'mean_return': np.mean(test_returns),
                    'std_return': np.std(test_returns),
                    'mean_sharpe': np.mean(test_sharpes),
                    'std_sharpe': np.std(test_sharpes),
                    'positive_periods': sum(1 for r in test_returns if r > 0),
                    'positive_periods_ratio': sum(1 for r in test_returns if r > 0) / len(test_returns)
                },
                'parameter_stability': self._analyze_parameter_stability(results),
                'period_results': results
            }

            logger.info(f"Walk-forward analysis completed. Out-of-sample mean Sharpe: {np.mean(test_sharpes):.4f}")
            return walk_forward_summary

        else:
            raise ValueError("No successful walk-forward periods")

    # 進階策略實現
    def _advanced_mean_reversion_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """進階均值回歸策略"""
        rsi_period = params.get('rsi_period', 14)
        bb_period = params.get('bb_period', 20)
        bb_std = params.get('bb_std', 2.0)
        atr_period = params.get('atr_period', 14)
        volatility_threshold = params.get('volatility_threshold', 0.02)

        # 計算指標
        rsi = self.indicators.calculate_rsi(data['close'], rsi_period)
        bb = self.indicators.calculate_bollinger_bands(data['close'], bb_period, bb_std)
        atr = self.indicators.calculate_atr(data['high'], data['low'], data['close'], atr_period)

        # 計算波動率
        returns = data['close'].pct_change()
        volatility = returns.rolling(20).std()

        # 生成信號
        close = data['close']

        # 進場信號：價格觸及下布林帶 + RSI超賣 + 低波動率
        buy_conditions = (
            (close <= bb['lower']) &
            (rsi < 30) &
            (volatility < volatility_threshold)
        )

        # 出場信號：價格觸及上布林帶 + RSI超買
        sell_conditions = (
            (close >= bb['upper']) &
            (rsi > 70)
        )

        # 避免連續信號
        buy_signals = buy_conditions & (~buy_conditions.shift(1).fillna(False))
        sell_signals = sell_conditions & (~sell_conditions.shift(1).fillna(False))

        return pd.DataFrame({
            'entries': buy_signals,
            'exits': sell_signals
        }, index=data.index)

    def _dual_rsi_confluence_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """雙RSI匯流策略"""
        fast_rsi_period = params.get('fast_rsi_period', 14)
        slow_rsi_period = params.get('slow_rsi_period', 28)
        oversold = params.get('oversold', 25)
        overbought = params.get('overbought', 75)

        # 計算雙RSI
        fast_rsi = self.indicators.calculate_rsi(data['close'], fast_rsi_period)
        slow_rsi = self.indicators.calculate_rsi(data['close'], slow_rsi_period)

        # 進場信號：快慢RSI都超賣且開始上升
        buy_conditions = (
            (fast_rsi < oversold) &
            (slow_rsi < oversold) &
            (fast_rsi > fast_rsi.shift(1)) &
            (slow_rsi > slow_rsi.shift(1))
        )

        # 出場信號：快慢RSI都超買且開始下降
        sell_conditions = (
            (fast_rsi > overbought) &
            (slow_rsi > overbought) &
            (fast_rsi < fast_rsi.shift(1)) &
            (slow_rsi < slow_rsi.shift(1))
        )

        return pd.DataFrame({
            'entries': buy_conditions,
            'exits': sell_conditions
        }, index=data.index)

    def _ichimoku_cloud_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """一目均衡表策略"""
        # 簡化版一目均衡表計算
        tenkan_period = params.get('tenkan_period', 9)
        kijun_period = params.get('kijun_period', 26)

        high = data['high']
        low = data['low']
        close = data['close']

        # 轉換線 (Tenkan-sen)
        tenkan_high = high.rolling(window=tenkan_period).max()
        tenkan_low = low.rolling(window=tenkan_period).min()
        tenkan = (tenkan_high + tenkan_low) / 2

        # 基準線 (Kijun-sen)
        kijun_high = high.rolling(window=kijun_period).max()
        kijun_low = low.rolling(window=kijun_period).min()
        kijun = (kijun_high + kijun_low) / 2

        # 進場信號：轉換線上穿基準線
        buy_signals = (tenkan > kijun) & (tenkan.shift(1) <= kijun.shift(1))

        # 出場信號：轉換線下穿基準線
        sell_signals = (tenkan < kijun) & (tenkan.shift(1) >= kijun.shift(1))

        return pd.DataFrame({
            'entries': buy_signals,
            'exits': sell_signals
        }, index=data.index)

    def _adx_momentum_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """ADX動量策略"""
        adx_period = params.get('adx_period', 14)
        adx_threshold = params.get('adx_threshold', 25)

        # 簡化ADX計算
        high = data['high']
        low = data['low']
        close = data['close']

        # 計算True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # 計算Directional Movement
        dm_plus = np.where((high - high.shift(1)) > (low.shift(1) - low),
                         np.maximum(high - high.shift(1), 0), 0)
        dm_minus = np.where((low.shift(1) - low) > (high - high.shift(1)),
                           np.maximum(low.shift(1) - low, 0), 0)

        # 平滑處理
        atr = pd.Series(tr).rolling(window=adx_period).mean()
        di_plus = 100 * pd.Series(dm_plus).rolling(window=adx_period).mean() / atr
        di_minus = 100 * pd.Series(dm_minus).rolling(window=adx_period).mean() / atr

        # 計算ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(window=adx_period).mean()

        # 進場信號：ADX大於閾值且DI+上穿DI-
        buy_signals = (adx > adx_threshold) & (di_plus > di_minus) & (di_plus.shift(1) <= di_minus.shift(1))

        # 出場信號：ADX大於閾值且DI-上穿DI+
        sell_signals = (adx > adx_threshold) & (di_minus > di_plus) & (di_minus.shift(1) <= di_plus.shift(1))

        return pd.DataFrame({
            'entries': buy_signals,
            'exits': sell_signals
        }, index=data.index)

    def _atr_volatility_breakout_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """ATR波動率突破策略"""
        atr_period = params.get('atr_period', 14)
        multiplier = params.get('multiplier', 2.0)

        # 計算ATR
        atr = self.indicators.calculate_atr(data['high'], data['low'], data['close'], atr_period)

        # 計算突破價位
        close = data['close']
        previous_close = close.shift(1)

        # 進場信號：價格突破上軌
        buy_signals = close > (previous_close + (atr * multiplier))

        # 出場信號：價格突破下軌
        sell_signals = close < (previous_close - (atr * multiplier))

        return pd.DataFrame({
            'entries': buy_signals,
            'exits': sell_signals
        }, index=data.index)

    def _multi_timeframe_rsi_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """多時間框架RSI策略"""
        daily_period = params.get('daily_period', 14)
        weekly_period = params.get('weekly_period', 12)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        # 計算日RSI
        daily_rsi = self.indicators.calculate_rsi(data['close'], daily_period)

        # 計算週RSI (簡化計算)
        weekly_close = data['close'].resample('W').last()
        weekly_rsi = self.indicators.calculate_rsi(weekly_close, weekly_period)
        weekly_rsi = weekly_rsi.reindex(data.index, method='ffill')

        # 進場信號：日RSI和週RSI都超賣且開始上升
        buy_conditions = (
            (daily_rsi < oversold) &
            (weekly_rsi < oversold) &
            (daily_rsi > daily_rsi.shift(1))
        )

        # 出場信號：日RSI和週RSI都超買且開始下降
        sell_conditions = (
            (daily_rsi > overbought) &
            (weekly_rsi > overbought) &
            (daily_rsi < daily_rsi.shift(1))
        )

        return pd.DataFrame({
            'entries': buy_conditions,
            'exits': sell_conditions
        }, index=data.index)

    def _vix_reversion_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """VIX回歸策略"""
        # 這裡使用價格波動率作為VIX代理
        vix_period = params.get('vix_period', 20)
        high_vix_threshold = params.get('high_vix_threshold', 30)
        low_vix_threshold = params.get('low_vix_threshold', 15)

        # 計算代理VIX（價格波動率）
        returns = data['close'].pct_change()
        proxy_vix = returns.rolling(window=vix_period).std() * np.sqrt(252) * 100

        # 進場信號：高波動率後的均值回歸
        buy_conditions = (proxy_vix > high_vix_threshold) & (proxy_vix < proxy_vix.shift(1))

        # 出場信號：低波動率後的趨勢跟隨
        sell_conditions = (proxy_vix < low_vix_threshold) & (data['close'] < data['close'].shift(1))

        return pd.DataFrame({
            'entries': buy_conditions,
            'exits': sell_conditions
        }, index=data.index)

    def _pair_trading_signals(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """配對交易策略"""
        # 這裡使用單一資產的均值回歸作為簡化
        lookback_period = params.get('lookback_period', 20)
        entry_threshold = params.get('entry_threshold', 2.0)
        exit_threshold = params.get('exit_threshold', 0.5)

        # 計算價格和移動平均
        close = data['close']
        ma = close.rolling(window=lookback_period).mean()

        # 計算Z-score
        std = close.rolling(window=lookback_period).std()
        z_score = (close - ma) / std

        # 進場信號：價格顯著低於均值
        buy_signals = z_score < -entry_threshold

        # 出場信號：價格回歸均值
        sell_signals = abs(z_score) < exit_threshold

        return pd.DataFrame({
            'entries': buy_signals,
            'exits': sell_signals
        }, index=data.index)

    # 輔助方法
    def _validate_portfolio_data(self, data_dict: Dict[str, pd.DataFrame]) -> None:
        """驗證投資組合數據"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']

        for symbol, data in data_dict.items():
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns for {symbol}: {missing_columns}")

            if len(data) < 20:
                raise ValueError(f"Insufficient data for {symbol}: {len(data)} (minimum 20 required)")

    def _execute_portfolio_backtest(
        self,
        data_dict: Dict[str, pd.DataFrame],
        signals_dict: Dict[str, pd.DataFrame],
        weights: Dict[str, float]
    ) -> Dict[str, BacktestResult]:
        """執行投資組合回測"""
        portfolio_results = {}

        for symbol, data in data_dict.items():
            signals = signals_dict[symbol]
            weight = weights.get(symbol, 0)

            if weight > 0:
                # 創建回測配置（考慮權重）
                portfolio_config = EnhancedBacktestConfig(
                    initial_cash=self.config.initial_cash * weight,
                    fees=self.config.fees,
                    slippage=self.config.slippage,
                    stop_loss=self.config.stop_loss,
                    take_profit=self.config.take_profit,
                    max_position_size=min(1.0, weight * 1.2),  # 稍微放寬以避免分數問題
                    risk_free_rate=self.config.risk_free_rate
                )

                # 執行單個資產回測
                result = self._backtest_with_config(data, signals, symbol, portfolio_config)
                portfolio_results[symbol] = result

        return portfolio_results

    def _backtest_with_config(
        self,
        data: pd.DataFrame,
        signals: pd.DataFrame,
        symbol: str,
        config: EnhancedBacktestConfig
    ) -> BacktestResult:
        """使用指定配置執行回測"""
        start_time = time.time()

        # 使用VectorBT執行回測
        portfolio = vbt.Portfolio.from_signals(
            close=data['close'],
            entries=signals['entries'],
            exits=signals['exits'],
            init_cash=config.initial_cash,
            fees=config.fees,
            slippage=config.slippage,
            freq='1D'
        )

        # 計算性能指標
        metrics = self._calculate_enhanced_metrics(portfolio, data, config)

        # 創建結果對象
        result = BacktestResult(
            symbol=symbol,
            strategy_name="Portfolio",
            parameters=config.__dict__,
            **metrics,
            equity_curve=portfolio.value(),
            returns=portfolio.returns(),
            trades=self._extract_trades(portfolio),
            signals=signals,
            start_date=data.index[0].strftime('%Y-%m-%d'),
            end_date=data.index[-1].strftime('%Y-%m-%d'),
            data_points=len(data),
            execution_time=time.time() - start_time
        )

        return result

    def _calculate_enhanced_metrics(
        self,
        portfolio: vbt.Portfolio,
        data: pd.DataFrame,
        config: EnhancedBacktestConfig
    ) -> Dict[str, float]:
        """計算增強性能指標"""
        returns = portfolio.returns()

        # 基本指標
        total_return = float(portfolio.total_return())
        annual_return = float(returns.mean() * 252)
        max_drawdown = float(portfolio.max_drawdown())

        # Sharpe比率（3%無風險利率）
        excess_returns = returns - config.risk_free_rate / 252
        sharpe_ratio = float(excess_returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0

        # 交易統計
        trades = portfolio.trades
        win_rate = float(trades.win_rate()) if len(trades) > 0 else 0.0
        profit_factor = float(trades.profit_factor()) if len(trades) > 0 else 0.0
        total_trades = len(trades.records_readable) if len(trades) > 0 else 0

        # 進階指標
        sortino_ratio = self._calculate_sortino_ratio(returns, config.risk_free_rate)
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

    def _calculate_advanced_risk_metrics(
        self,
        returns: pd.Series,
        config: EnhancedBacktestConfig
    ) -> AdvancedRiskMetrics:
        """計算進階風險指標"""
        # Value at Risk
        if config.var_method == "historical":
            var_95 = float(np.percentile(returns, (1 - config.var_confidence) * 100))
            var_99 = float(np.percentile(returns, (1 - 0.99) * 100))
        else:
            # Parametric method
            mean_ret = returns.mean()
            std_ret = returns.std()
            var_95 = float(mean_ret + stats.norm.ppf(1 - config.var_confidence) * std_ret)
            var_99 = float(mean_ret + stats.norm.ppf(0.01) * std_ret)

        # Expected Shortfall
        es_95 = float(returns[returns <= var_95].mean()) if (returns <= var_95).any() else 0.0

        # Sortino Ratio
        sortino_ratio = self._calculate_sortino_ratio(returns, config.risk_free_rate)

        # Calmar Ratio
        total_return = (1 + returns).prod() - 1
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        calmar_ratio = float(total_return / abs(max_drawdown)) if max_drawdown != 0 else 0.0

        # Information Ratio and Tracking Error (需要基準)
        # 這裡使用0作為基準，實際應用中應該使用市場基準
        information_ratio = float(returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0.0
        tracking_error = float(returns.std() * np.sqrt(252))

        return AdvancedRiskMetrics(
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=es_95,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            information_ratio=information_ratio,
            tracking_error=tracking_error,
            beta=0.0,  # 需要基準計算
            alpha=0.0,  # 需要基準計算
            max_drawdown_duration=0,  # 需要詳細計算
            recovery_time=0  # 需要詳細計算
        )

    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float) -> float:
        """計算Sortino比率"""
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        downside_deviation = downside_returns.std()

        return float(excess_returns.mean() / downside_deviation * np.sqrt(252))

    def _analyze_parameter_stability(self, results: List[Dict]) -> Dict[str, Any]:
        """分析參數穩定性"""
        # 提取參數值
        param_names = list(results[0]['optimal_params'].keys())
        param_values = {name: [] for name in param_names}

        for result in results:
            for name, value in result['optimal_params'].items():
                param_values[name].append(value)

        # 計算穩定性指標
        stability_analysis = {}
        for name, values in param_values.items():
            if values:
                stability_analysis[name] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'cv': np.std(values) / np.mean(values) if np.mean(values) != 0 else 0,
                    'min': np.min(values),
                    'max': np.max(values),
                    'range': np.max(values) - np.min(values)
                }

        return stability_analysis

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

    def _backtest_single_safe(
        self,
        data: pd.DataFrame,
        strategy: str,
        params: Dict[str, Any],
        symbol: str
    ) -> Optional[BacktestResult]:
        """安全的單一回測，包含錯誤處理"""
        try:
            signals = self._generate_signals(data, strategy, params)
            result = self._backtest_with_config(data, signals, symbol, self.config)
            return result
        except Exception as e:
            logger.warning(f"Backtest failed for params {params}: {e}")
            return None

    def _generate_signals(
        self,
        data: pd.DataFrame,
        strategy: str,
        parameters: Dict[str, Any]
    ) -> pd.DataFrame:
        """生成交易信號"""
        if strategy in self._strategy_registry:
            return self._strategy_registry[strategy](data, parameters)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _extract_trades(self, portfolio: vbt.Portfolio) -> pd.DataFrame:
        """提取交易記錄"""
        try:
            if len(portfolio.trades) > 0:
                return portfolio.trades.records_readable
            else:
                return pd.DataFrame()
        except:
            return pd.DataFrame()

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
            'available_strategies': list(self._strategy_registry.keys()),
            'config': {
                'initial_cash': self.config.initial_cash,
                'fees': self.config.fees,
                'slippage': self.config.slippage,
                'enable_parallel': self.config.enable_parallel,
                'max_workers': self.config.max_workers
            }
        }

# 便利函數
def create_enhanced_engine(config: Optional[EnhancedBacktestConfig] = None) -> EnhancedVectorBTEngine:
    """創建增強VectorBT引擎的便利函數"""
    return EnhancedVectorBTEngine(config)

def run_portfolio_backtest(
    data_dict: Dict[str, pd.DataFrame],
    strategy: str,
    parameters: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
    config: Optional[EnhancedBacktestConfig] = None
) -> Dict[str, BacktestResult]:
    """便利函數：投資組合回測"""
    engine = EnhancedVectorBTEngine(config)
    return engine.backtest_portfolio(data_dict, strategy, parameters, weights)

def run_walk_forward_analysis(
    data: pd.DataFrame,
    strategy: str,
    param_ranges: Dict[str, Union[List, range]],
    window_size: int = 504,
    step_size: int = 126,
    test_size: int = 63,
    symbol: str = "UNKNOWN"
) -> Dict[str, Any]:
    """便利函數：走前分析"""
    engine = EnhancedVectorBTEngine()
    return engine.walk_forward_analysis(data, strategy, param_ranges, window_size, step_size, test_size, symbol)