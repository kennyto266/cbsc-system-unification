#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速非價格技術分析引擎
GPU-Accelerated Non-Price Technical Analysis Engine

專為香港政府數據設計的非價格技術分析引擎
利用GPU加速計算HIBOR-RSI、貨幣基礎MACD等策略
"""

import numpy as np
import pandas as pd
import time
import logging
import sys
import os
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime

# GPU相關導入
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
try:
    from src.gpu.gpu_computation_core import get_gpu_computation_core
    from src.gpu.gpu_pipeline import get_gpu_pipeline
    from src.gpu.gpu_monitor import get_gpu_monitor
    from src.gpu.memory_manager import get_gpu_memory_manager
except ImportError:
    # 如果導入失敗，使用簡化版本
    logger = logging.getLogger(__name__)
    logger.warning("GPU模塊導入失敗，將使用CPU版本")
    get_gpu_computation_core = None
    get_gpu_pipeline = None
    get_gpu_monitor = None
    get_gpu_memory_manager = None

logger = logging.getLogger(__name__)

class GPUNonPriceTAEngine:
    """GPU加速非價格技術分析引擎"""

    def __init__(self, gpu_device: int = 0):
        """
        初始化非價格TA引擎

        Args:
            gpu_device: GPU设备ID
        """
        self.gpu_device = gpu_device
        self.gpu_available = True

        # 初始化GPU組件
        try:
            if get_gpu_computation_core is not None:
                self.gpu_core = get_gpu_computation_core(gpu_device)
                self.gpu_pipeline = get_gpu_pipeline(gpu_device)
                self.gpu_monitor = get_gpu_monitor(gpu_device)
                self.memory_manager = get_gpu_memory_manager(gpu_device)
                logger.info(f"GPU非價格TA引擎初始化完成，GPU設備: {gpu_device}")
            else:
                raise ImportError("GPU模塊不可用")
        except Exception as e:
            logger.warning(f"GPU初始化失敗，使用CPU版本: {e}")
            self.gpu_available = False
            self._init_cpu_version()

        # 策略參數
        self.strategies = {
            'hibor_rsi': {
                'rsi_period': 14,
                'oversold': 30,
                'overbought': 70,
                'signal_threshold': 0.3
            },
            'monetary_macd': {
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
                'trend_threshold': 0.02
            },
            'composite_momentum': {
                'weights': [0.4, 0.3, 0.2, 0.1],  # HIBOR, GDP, 貨幣基礎, 貿易
                'momentum_period': 10,
                'signal_threshold': 0.5
            },
            'interest_rate_arbitrage': {
                'rate_diff_threshold': 0.5,
                'trend_period': 20,
                'risk_adjustment': True
            }
        }

    def _init_cpu_version(self):
        """初始化CPU版本"""
        # 創建簡單的CPU版本GPU核心替代
        class SimpleCPUCore:
            def __init__(self):
                self.cp = np  # 使用NumPy作為CuPy替代

            def calculate_rsi_gpu(self, data, period=14):
                return self._calculate_rsi_cpu(data, period)

            def calculate_moving_average_gpu(self, data, period):
                return self._calculate_sma_cpu(data, period)

            def calculate_macd_gpu(self, data, fast, slow, signal):
                return self._calculate_macd_cpu(data, fast, slow, signal)

            def _calculate_rsi_cpu(self, data, period=14):
                delta = np.diff(data)
                gain = np.where(delta > 0, delta, 0)
                loss = np.where(delta < 0, -delta, 0)
                avg_gain = np.mean(gain[:period])
                avg_loss = np.mean(loss[:period])
                rs = avg_gain / (avg_loss + 1e-10)
                rsi = 100 - (100 / (1 + rs))
                return np.concatenate([np.array([50]), rsi * np.ones(len(data) - 1)])

            def _calculate_sma_cpu(self, data, period):
                result = np.convolve(data, np.ones(period)/period, mode='same')
                return result

            def _calculate_macd_cpu(self, data, fast, slow, signal):
                fast_ema = self._calculate_ema_cpu(data, fast)
                slow_ema = self._calculate_ema_cpu(data, slow)
                macd_line = fast_ema - slow_ema
                signal_line = self._calculate_ema_cpu(macd_line, signal)
                histogram = macd_line - signal_line
                return macd_line, signal_line, histogram

            def _calculate_ema_cpu(self, data, period):
                alpha = 2 / (period + 1)
                ema = np.zeros_like(data)
                ema[0] = data[0]
                for i in range(1, len(data)):
                    ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
                return ema

        self.gpu_core = SimpleCPUCore()
        self.gpu_pipeline = None
        self.gpu_monitor = None
        self.memory_manager = None

        logger.info(f"GPU非價格TA引擎初始化完成，GPU設備: {gpu_device}")

        # 性能統計
        self.performance_stats = {
            'total_calculations': 0,
            'gpu_calculation_time': 0,
            'cpu_fallback_count': 0,
            'memory_usage_peak': 0
        }

    def calculate_hibor_rsi_strategy(self, hibor_data: np.ndarray,
                                    stock_data: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        HIBOR-RSI策略 - 基於HIBOR利率的超買超賣策略

        Args:
            hibor_data: HIBOR利率數據
            stock_data: 股價數據（可選，用於趨勢確認）

        Returns:
            策略結果包含信號、技術指標等
        """
        start_time = time.time()

        try:
            params = self.strategies['hibor_rsi']

            # GPU計算HIBOR RSI
            hibor_rsi = self.gpu_core.calculate_rsi_gpu(hibor_data, params['rsi_period'])

            # 計算RSI變化率（動能指標）
            rsi_momentum = self._calculate_rsi_momentum(hibor_rsi)

            # 計算移動平均（趨勢）
            rsi_ma = self.gpu_core.calculate_moving_average_gpu(hibor_rsi, params['rsi_period'])

            # 生成信號
            signals = self._generate_rsi_signals(hibor_rsi, rsi_ma, params)

            # 如果有股價數據，進行趨勢確認
            trend_confirmation = None
            if stock_data is not None:
                trend_confirmation = self._confirm_trend_with_price(
                    hibor_rsi, stock_data, params
                )

            calculation_time = time.time() - start_time
            self.performance_stats['total_calculations'] += 1
            self.performance_stats['gpu_calculation_time'] += calculation_time

            return {
                'strategy_name': 'HIBOR_RSI',
                'signals': signals,
                'indicators': {
                    'rsi': hibor_rsi,
                    'rsi_ma': rsi_ma,
                    'rsi_momentum': rsi_momentum,
                    'trend_confirmation': trend_confirmation
                },
                'parameters': params,
                'performance': {
                    'calculation_time': calculation_time,
                    'data_points': len(hibor_data)
                },
                'success': True
            }

        except Exception as e:
            logger.error(f"HIBOR-RSI策略計算失敗: {e}")
            self.performance_stats['cpu_fallback_count'] += 1
            return self._fallback_hibor_rsi(hibor_data, stock_data)

    def calculate_monetary_macd_strategy(self, monetary_data: np.ndarray,
                                         stock_data: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        貨幣基礎MACD策略 - 基於貨幣基礎的MACD策略

        Args:
            monetary_data: 貨幣基礎數據
            stock_data: 股價數據（可選）

        Returns:
            策略結果
        """
        start_time = time.time()

        try:
            params = self.strategies['monetary_macd']

            # GPU計算貨幣基礎MACD
            macd_line, signal_line, histogram = self.gpu_core.calculate_macd_gpu(
                monetary_data, params['fast_period'], params['slow_period'], params['signal_period']
            )

            # 計算MACD斜率（趨勢強度）
            macd_slope = self._calculate_macd_slope(macd_line)

            # 計算MACD動能
            macd_momentum = self._calculate_macd_momentum(macd_line, signal_line)

            # 生成信號
            signals = self._generate_macd_signals(
                macd_line, signal_line, histogram, macd_slope, params
            )

            # 貨幣擴張/緊縮檢測
            expansion_signals = self._detect_monetary_expansion(monetary_data, macd_line, params)

            calculation_time = time.time() - start_time
            self.performance_stats['total_calculations'] += 1
            self.performance_stats['gpu_calculation_time'] += calculation_time

            return {
                'strategy_name': 'MONETARY_MACD',
                'signals': signals,
                'indicators': {
                    'macd_line': macd_line,
                    'signal_line': signal_line,
                    'histogram': histogram,
                    'macd_slope': macd_slope,
                    'macd_momentum': macd_momentum,
                    'expansion_signals': expansion_signals
                },
                'parameters': params,
                'performance': {
                    'calculation_time': calculation_time,
                    'data_points': len(monetary_data)
                },
                'success': True
            }

        except Exception as e:
            logger.error(f"貨幣基礎MACD策略計算失敗: {e}")
            self.performance_stats['cpu_fallback_count'] += 1
            return self._fallback_monetary_macd(monetary_data, stock_data)

    def calculate_composite_momentum_strategy(self, gov_data: Dict[str, np.ndarray],
                                                stock_data: np.ndarray) -> Dict[str, Any]:
        """
        綜合動量策略 - 結合多種政府數據的動量策略

        Args:
            gov_data: 政府數據字典 {'hb': hibor, 'gd': gdp, 'mb': monetary, 'tr': trade}
            stock_data: 股價數據

        Returns:
            綜合策略結果
        """
        start_time = time.time()

        try:
            params = self.strategies['composite_momentum']
            weights = params['weights']

            # 計算各個數據源的動量指標
            momentum_indicators = {}

            # HIBOR動量
            if 'hb' in gov_data:
                hb_momentum = self._calculate_momentum_indicator(
                    gov_data['hb'], params['momentum_period']
                )
                momentum_indicators['hibor'] = hb_momentum

            # GDP動量
            if 'gd' in gov_data:
                gd_momentum = self._calculate_momentum_indicator(
                    gov_data['gd'], params['momentum_period']
                )
                momentum_indicators['gdp'] = gd_momentum

            # 貨幣基礎動量
            if 'mb' in gov_data:
                mb_momentum = self._calculate_momentum_indicator(
                    gov_data['mb'], params['momentum_period']
                )
                momentum_indicators['monetary'] = mb_momentum

            # 貿易動量
            if 'tr' in gov_data:
                tr_momentum = self._calculate_momentum_indicator(
                    gov_data['tr'], params['momentum_period']
                )
                momentum_indicators['trade'] = tr_momentum

            # 加權綜合
            composite_momentum = self._calculate_composite_momentum(
                momentum_indicators, weights
            )

            # 生成信號
            signals = self._generate_composite_momentum_signals(
                composite_momentum, params
            )

            # 風險評估
            risk_assessment = self._assess_strategy_risk(momentum_indicators, composite_momentum)

            calculation_time = time.time() - start_time
            self.performance_stats['total_calculations'] += 1
            self.performance_stats['gpu_calculation_time'] += calculation_time

            return {
                'strategy_name': 'COMPOSITE_MOMENTUM',
                'signals': signals,
                'indicators': {
                    'momentum_indicators': momentum_indicators,
                    'composite_momentum': composite_momentum,
                    'risk_assessment': risk_assessment
                },
                'parameters': params,
                'performance': {
                    'calculation_time': calculation_time,
                    'data_sources': len(momentum_indicators)
                },
                'success': True
            }

        except Exception as e:
            logger.error(f"綜合動量策略計算失敗: {e}")
            self.performance_stats['cpu_fallback_count'] += 1
            return self._fallback_composite_momentum(gov_data, stock_data)

    def calculate_interest_rate_arbitrage_strategy(self, hibor_data: np.ndarray,
                                                      monetary_data: np.ndarray) -> Dict[str, Any]:
        """
        利率套利策略 - 基於利率差的套利機會

        Args:
            hibor_data: HIBOR利率數據
            monetary_data: 貨幣基礎數據

        Returns:
        """
        start_time = time.time()

        try:
            params = self.strategies['interest_rate_arbitrage']

            # 計算利率變化率
            hibor_rate_change = self._calculate_rate_change(hibor_data)
            monetary_rate_change = self._calculate_rate_change(monetary_data)

            # 計算利率差
            rate_spread = hibor_rate_change - monetary_rate_change

            # 計算移動平均（平滑處理）
            spread_ma = self.gpu_core.calculate_moving_average_gpu(rate_spread, params['trend_period'])

            # 生成套利信號
            signals = self._generate_arbitrage_signals(rate_spread, spread_ma, params)

            # 計算套利機會評分
            opportunity_score = self._calculate_arbitrage_opportunity(rate_spread, params)

            calculation_time = time.time() - start_time
            self.performance_stats['total_calculations'] += 1
            self.performance_stats['gpu_calculation_time'] += calculation_time

            return {
                'strategy_name': 'INTEREST_RATE_ARBITRAGE',
                'signals': signals,
                'indicators': {
                    'hibor_rate_change': hibor_rate_change,
                    'monetary_rate_change': monetary_rate_change,
                    'rate_spread': rate_spread,
                    'spread_ma': spread_ma,
                    'opportunity_score': opportunity_score
                },
                'parameters': params,
                'performance': {
                    'calculation_time': calculation_time,
                    'data_points': len(hibor_data)
                },
                'success': True
            }

        except Exception as e:
            logger.error(f"利率套利策略計算失敗: {e}")
            self.performance_stats['cpu_fallback_count'] += 1
            return self._fallback_interest_rate_arbitrage(hibor_data, monetary_data)

    def _calculate_rsi_momentum(self, rsi: np.ndarray) -> np.ndarray:
        """計算RSI動量"""
        # 使用GPU計算差分
        return self.gpu_core.cp.diff(rsi) if len(rsi) > 1 else self.gpu_core.cp.zeros_like(rsi)

    def _calculate_macd_slope(self, macd_line: np.ndarray) -> np.ndarray:
        """計算MACD斜率"""
        return self.gpu_core.cp.diff(macd_line) if len(macd_line) > 1 else self.gpu_core.cp.zeros_like(macd_line)

    def _calculate_macd_momentum(self, macd_line: np.ndarray, signal_line: np.ndarray) -> np.ndarray:
        """計算MACD動能"""
        return macd_line - signal_line

    def _generate_rsi_signals(self, rsi: np.ndarray, rsi_ma: np.ndarray, params: Dict) -> np.ndarray:
        """生成RSI信號"""
        signals = self.gpu_core.cp.zeros_like(rsi)

        # 超賣信號 - 使用NumPy操作替代pandas shift
        rsi_prev = self.gpu_core.cp.roll(rsi, 1)
        oversold_signals = (rsi < params['oversold']) & (rsi_prev >= params['oversold'])

        # 超買信號
        overbought_signals = (rsi > params['overbought']) & (rsi_prev <= params['overbought'])

        # 動能確認信號
        momentum_confirmation = self.gpu_core.cp.abs(rsi - rsi_ma) > params['signal_threshold']

        # 綜合信號
        buy_signals = oversold_signals & momentum_confirmation
        sell_signals = overbought_signals & momentum_confirmation

        # 轉換為數值信號 (1=買入, -1=賣出, 0=持有)
        signals[buy_signals] = 1
        signals[sell_signals] = -1

        return signals

    def _generate_macd_signals(self, macd_line: np.ndarray, signal_line: np.ndarray,
                                histogram: np.ndarray, macd_slope: np.ndarray,
                                params: Dict) -> np.ndarray:
        """生成MACD信號"""
        signals = self.gpu_core.cp.zeros_like(macd_line)

        # 使用NumPy roll替代pandas shift
        macd_prev = self.gpu_core.cp.roll(macd_line, 1)
        signal_prev = self.gpu_core.cp.roll(signal_line, 1)

        # 黃金交叉向上
        golden_cross = (macd_line > signal_line) & (macd_prev <= signal_prev)

        # 黃金交叉向下
        death_cross = (macd_line < signal_line) & (macd_prev >= signal_prev)

        # 趨勢確認
        trend_confirmation = self.gpu_core.cp.abs(macd_slope) > params['trend_threshold']

        # 動能確認
        momentum_confirmation = self.gpu_core.cp.abs(histogram) > params['trend_threshold']

        # 綜合信號
        buy_signals = golden_cross & trend_confirmation & momentum_confirmation
        sell_signals = death_cross & (-trend_confirmation) & (-momentum_confirmation)

        signals[buy_signals] = 1
        signals[sell_signals] = -1

        return signals

    def _calculate_momentum_indicator(self, data: np.ndarray, period: int) -> np.ndarray:
        """計算動量指標"""
        # 使用GPU計算百分比變化
        return (data / self.gpu_core.cp.roll(data, period) - 1) * 100

    def _calculate_composite_momentum(self, momentum_indicators: Dict[str, np.ndarray],
                                        weights: List[float]) -> np.ndarray:
        """計算綜合動量"""
        composite = self.gpu_core.cp.zeros_like(list(momentum_indicators.values())[0])

        total_weight = 0
        for i, (source, momentum) in enumerate(momentum_indicators.items()):
            if i < len(weights):
                composite += momentum * weights[i]
                total_weight += weights[i]

        if total_weight > 0:
            composite /= total_weight

        return composite

    def _generate_composite_momentum_signals(self, composite_momentum: np.ndarray,
                                            params: Dict) -> np.ndarray:
        """生成綜合動量信號"""
        signals = self.gpu_core.cp.zeros_like(composite_momentum)

        # 動能向上信號
        momentum_up = composite_momentum > params['signal_threshold']

        # 動能向下信號
        momentum_down = composite_momentum < -params['signal_threshold']

        signals[momentum_up] = 1
        signals[momentum_down] = -1

        return signals

    def _calculate_rate_change(self, data: np.ndarray) -> np.ndarray:
        """計算變化率"""
        return self.gpu_core.cp.diff(data) / self.gpu_core.cp.roll(data, 1) * 100

    def _generate_arbitrage_signals(self, rate_spread: np.ndarray, spread_ma: np.ndarray,
                                     params: Dict) -> np.ndarray:
        """生成套利信號"""
        signals = self.gpu_core.cp.zeros_like(rate_spread)

        # 套利機會
        opportunity = self.gpu_core.cp.abs(rate_spread) > params['rate_diff_threshold']

        # 趨勢確認
        trend_direction = rate_spread > spread_ma

        signals[opportunity & trend_direction] = 1
        signals[opportunity & (-trend_direction)] = -1

        return signals

    def _calculate_arbitrage_opportunity(self, rate_spread: np.ndarray, params: Dict) -> np.ndarray:
        """計算套利機會評分"""
        return self.gpu_core.cp.abs(rate_spread) * 100  # 簡化評分

    def _assess_strategy_risk(self, momentum_indicators: Dict[str, np.ndarray],
                             composite_momentum: np.ndarray) -> Dict[str, Any]:
        """評估策略風險"""
        # 計算各個指標的波動性
        volatilities = {}
        for source, momentum in momentum_indicators.items():
            volatilities[source] = self.gpu_core.cp.std(momentum)

        composite_volatility = self.gpu_core.cp.std(composite_momentum)

        # 風險評分 (波動性越高，風險越高)
        risk_score = composite_volatility / 100  # 簡化風險評分

        return {
            'volatilities': volatilities,
            'composite_volatility': composite_volatility,
            'risk_score': risk_score,
            'risk_level': 'HIGH' if risk_score > 0.02 else 'MEDIUM' if risk_score > 0.01 else 'LOW'
        }

    def _confirm_trend_with_price(self, rsi: np.ndarray, stock_data: np.ndarray,
                                 params: Dict) -> bool:
        """用股價確認趨勢"""
        # 計算股價簡單移動平均
        try:
            price_ma = self.gpu_core.calculate_moving_average_gpu(stock_data, 20)

            # 計算趨勢相關性
            rsi_normalized = (rsi - rsi.mean()) / (rsi.std() + 1e-8)
            price_normalized = (stock_data - price_ma) / (price_ma.std() + 1e-8)

            correlation = np.corrcoef(rsi_normalized, price_normalized)[0, 1]

            return abs(correlation) > 0.3  # 相關性閾值

        except:
            return False

    def _detect_monetary_expansion(self, monetary_data: np.ndarray, macd_line: np.ndarray,
                                  params: Dict) -> np.ndarray:
        """檢測貨幣擴張/緊縮"""
        # 簡化實現：基於MACD判斷
        expansion = macd_line > 0

        return expansion.astype(float)

    # CPU後備方法
    def _fallback_hibor_rsi(self, hibor_data: np.ndarray, stock_data: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """HIBOR-RSI CPU後備方法"""
        # CPU實現...
        return {'success': False, 'error': 'CPU fallback not implemented', 'strategy_name': 'HIBOR_RSI'}

    def _fallback_monetary_macd(self, monetary_data: np.ndarray, stock_data: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """貨幣基礎MACD CPU後備方法"""
        # CPU實現...
        return {'success': False, 'error': 'CPU fallback not implemented', 'strategy_name': 'MONETARY_MACD'}

    def _fallback_composite_momentum(self, gov_data: Dict[str, np.ndarray], stock_data: np.ndarray) -> Dict[str, Any]:
        """綜合動量 CPU後備方法"""
        # CPU實現...
        return {'success': False, 'error': 'CPU fallback not implemented', 'strategy_name': 'COMPOSITE_MOMENTUM'}

    def _fallback_interest_rate_arbitrage(self, hibor_data: np.ndarray, monetary_data: np.ndarray) -> Dict[str, Any]:
        """利率套利 CPU後備方法"""
        # CPU實現...
        return {'success': False, 'error': 'CPU fallback not implemented', 'strategy_name': 'INTEREST_RATE_ARBITRAGE'}

    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        return {
            'total_calculations': self.performance_stats['total_calculations'],
            'gpu_calculation_time': self.performance_stats['gpu_calculation_time'],
            'cpu_fallback_count': self.performance_stats['cpu_fallback_count'],
            'average_gpu_time': (
                self.performance_stats['gpu_calculation_time'] /
                max(1, self.performance_stats['total_calculations'])
            ),
            'gpu_success_rate': 1 - (
                self.performance_stats['cpu_fallback_count'] /
                max(1, self.performance_stats['total_calculations'])
            )
        }

def main():
    """測試GPU非價格TA引擎"""
    print("=" * 60)
    print("GPU加速非價格技術分析引擎測試")
    print("=" * 60)

    try:
        # 初始化引擎
        engine = GPUNonPriceTAEngine(gpu_device=0)

        # 生成測試數據
        np.random.seed(42)
        test_data_length = 252

        # HIBOR測試數據
        hibor_data = np.random.uniform(3.0, 5.0, test_data_length).astype(np.float32)

        # 貨幣基礎測試數據
        monetary_data = np.random.uniform(1800, 2200, test_data_length).astype(np.float32)

        # 股價測試數據
        stock_data = np.random.uniform(300, 700, test_data_length).astype(np.float32)

        # 其他政府數據
        gdp_data = np.random.uniform(2.0, 4.0, test_data_length).astype(np.float32)
        trade_data = np.random.uniform(0.5, 1.5, test_data_length).astype(np.float32)

        gov_data = {
            'hb': hibor_data,
            'gd': gdp_data,
            'mb': monetary_data,
            'tr': trade_data
        }

        # 測試各種策略
        print("\n測試HIBOR-RSI策略...")
        hibor_result = engine.calculate_hibor_rsi_strategy(hibor_data, stock_data)

        print("\n測試貨幣基礎MACD策略...")
        monetary_result = engine.calculate_monetary_macd_strategy(monetary_data, stock_data)

        print("\n測試綜合動量策略...")
        composite_result = engine.calculate_composite_momentum_strategy(gov_data, stock_data)

        print("\n測試利率套利策略...")
        arbitrage_result = engine.calculate_interest_rate_arbitrage_strategy(hibor_data, monetary_data)

        # 顯示結果
        results = [hibor_result, monetary_result, composite_result, arbitrage_result]

        print("\n📊 測試結果摘要:")
        for result in results:
            if result.get('success', False):
                print(f"  {result['strategy_name']}: ✅ 成功")
                if 'performance' in result:
                    print(f"    計算時間: {result['performance']['calculation_time']:.4f}秒")
                    print(f"    數據點數: {result['performance']['data_points']}")
            else:
                print(f"  {result.get('strategy_name', 'Unknown')}: ❌ 失敗")

        # 性能摘要
        print("\n🚀 性能摘要:")
        perf = engine.get_performance_summary()
        print(f"  總計算次數: {perf['total_calculations']}")
        print(f"  GPU計算時間: {perf['gpu_calculation_time']:.4f}秒")
        print(f"  CPU後備次數: {perf['cpu_fallback_count']}")
        print(f"  平均GPU時間: {perf['average_gpu_time']:.4f}秒")
        print(f"  GPU成功率: {perf['gpu_success_rate']*100:.1f}%")

    except Exception as e:
        logger.error(f"測試失敗: {e}")
        print(f"測試失敗: {e}")

if __name__ == "__main__":
    main()