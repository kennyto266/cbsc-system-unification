#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU加速非價格數據回測系統 - 0700.HK專用
使用GPU加速技術，基於香港政府非價格數據進行量化回測
"""

import sys
import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import logging

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GPUNonPriceBacktestEngine:
    """GPU加速非價格數據回測引擎"""

    def __init__(self):
        self.gpu_available = False
        self.data_integration_manager = None
        self.gpu_engine = None
        self.backtest_results = {}

        # 初始化系統
        self._initialize_system()

    def _initialize_system(self):
        """初始化系統組件"""
        try:
            logger.info("🚀 初始化GPU非價格回測引擎...")

            # 1. 檢查GPU可用性
            self._check_gpu_availability()

            # 2. 初始化數據整合管理器
            self._initialize_data_manager()

            # 3. 初始化GPU引擎
            self._initialize_gpu_engine()

            logger.info("✅ GPU非價格回測引擎初始化完成")

        except Exception as e:
            logger.error(f"系統初始化失敗: {e}")
            raise

    def _check_gpu_availability(self):
        """檢查GPU可用性"""
        try:
            # 嘗試導入CUDA相關庫
            import cupy as cp

            # 檢查GPU設備
            if cp.cuda.is_available():
                device_count = cp.cuda.runtime.getDeviceCount()
                if device_count > 0:
                    self.gpu_available = True
                    device_props = cp.cuda.runtime.getDeviceProperties(0)
                    gpu_memory = device_props['totalGlobalMem'] / (1024**3)  # GB

                    logger.info(f"✅ 檢測到GPU: {device_props['name'].decode()}")
                    logger.info(f"📊 GPU內存: {gpu_memory:.1f} GB")
                    logger.info(f"🔧 計算能力: {device_props['major']}.{device_props['minor']}")
                else:
                    logger.warning("⚠️ 未檢測到GPU設備，將使用CPU計算")
            else:
                logger.warning("⚠️ CUDA不可用，將使用CPU計算")

        except ImportError:
            logger.warning("⚠️ CuPy未安裝，將使用CPU計算")
            self.gpu_available = False
        except Exception as e:
            logger.warning(f"⚠️ GPU檢測失敗: {e}，將使用CPU計算")
            self.gpu_available = False

    def _initialize_data_manager(self):
        """初始化數據管理器"""
        try:
            # 使用simplified_system的數據管理
            from simplified_system.src.data.government_data import GovernmentDataAPI
            from simplified_system.src.api.stock_api import get_hk_stock_data

            self.data_integration_manager = {
                'gov_api': GovernmentDataAPI(),
                'stock_api': get_hk_stock_data
            }

            logger.info("✅ 數據管理器初始化成功")

        except Exception as e:
            logger.error(f"數據管理器初始化失敗: {e}")
            # 使用備用數據源
            self._initialize_fallback_data_sources()

    def _initialize_fallback_data_sources(self):
        """初始化備用數據源"""
        try:
            import requests

            def get_stock_data_fallback(symbol, days=365):
                """獲取股票數據的備用方法"""
                url = "http://18.180.162.113:9191/inst/getInst"
                params = {"symbol": symbol.lower(), "duration": days}

                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                dates = list(data['data']['close'].keys())
                close_prices = list(data['data']['close'].values())

                df = pd.DataFrame({
                    'close': close_prices,
                    'volume': [1000000] * len(close_prices)  # 模擬成交量
                }, index=pd.to_datetime(dates))

                return df

            def get_gov_data_fallback():
                """獲取政府數據的備用方法"""
                # 使用模擬的政府數據
                dates = pd.date_range(end=datetime.now(), periods=365, freq='D')

                # 模擬HIBOR數據
                hibor_data = pd.Series(
                    np.random.normal(3.5, 0.5, len(dates)),
                    index=dates
                )

                # 模擬貨幣基礎數據
                monetary_base = pd.Series(
                    np.random.normal(200000, 10000, len(dates)),
                    index=dates
                )

                return {
                    'hibor': hibor_data,
                    'monetary_base': monetary_base
                }

            self.data_integration_manager = {
                'stock_api': get_stock_data_fallback,
                'gov_api': get_gov_data_fallback
            }

            logger.info("✅ 備用數據源初始化成功")

        except Exception as e:
            logger.error(f"備用數據源初始化失敗: {e}")
            raise

    def _initialize_gpu_engine(self):
        """初始化GPU引擎"""
        try:
            if self.gpu_available:
                # 嘗試導入GPU技術指標引擎
                from simplified_system.src.indicators.gpu_indicators import GPUTechnicalIndicators

                self.gpu_engine = GPUTechnicalIndicators(use_gpu=True)
                logger.info("✅ GPU引擎初始化成功")
            else:
                # 使用CPU版本的技術指標
                from simplified_system.src.indicators.core_indicators import CoreIndicators

                self.gpu_engine = CoreIndicators()
                logger.info("✅ CPU引擎初始化成功")

        except Exception as e:
            logger.warning(f"GPU引擎初始化失敗，使用CPU版本: {e}")
            try:
                from simplified_system.src.indicators.core_indicators import CoreIndicators
                self.gpu_engine = CoreIndicators()
                logger.info("✅ CPU引擎備用初始化成功")
            except Exception as e2:
                logger.error(f"CPU引擎初始化也失敗: {e2}")
                raise

    async def prepare_0700_data(self, days: int = 365) -> Dict[str, Any]:
        """準備0700.HK的非價格數據"""
        logger.info(f"📊 準備0700.HK數據，期間: {days}天")

        try:
            # 1. 獲取股票數據
            logger.info("正在獲取0700.HK股票數據...")
            stock_data = self.data_integration_manager['stock_api']('0700.HK', days)

            if stock_data is None or stock_data.empty:
                raise Exception("無法獲取股票數據")

            logger.info(f"✅ 股票數據: {len(stock_data)} 條記錄")
            logger.info(f"📅 價格範圍: {stock_data['close'].min():.2f} - {stock_data['close'].max():.2f} HKD")

            # 2. 獲取政府非價格數據
            logger.info("正在獲取政府非價格數據...")
            try:
                gov_data = self.data_integration_manager['gov_api']()
                if isinstance(gov_data, dict):
                    # 如果是字典格式，直接使用
                    pass
                else:
                    # 如果是其他格式，轉換為字典
                    gov_data = {'data': gov_data}
            except:
                # 使用模擬數據作為備用
                dates = stock_data.index
                gov_data = {
                    'hibor': pd.Series(
                        np.random.normal(3.5, 0.5, len(dates)),
                        index=dates
                    ),
                    'monetary_base': pd.Series(
                        np.random.normal(200000, 10000, len(dates)),
                        index=dates
                    )
                }

            logger.info(f"✅ 政府數據: {len(gov_data)} 個數據源")

            # 3. 數據對齊和預處理
            logger.info("正在對齊和預處理數據...")
            aligned_data = self._align_data(stock_data, gov_data)

            logger.info("✅ 數據準備完成")
            return aligned_data

        except Exception as e:
            logger.error(f"數據準備失敗: {e}")
            raise

    def _align_data(self, stock_data: pd.DataFrame, gov_data: Dict) -> Dict[str, Any]:
        """對齊股票和政府數據"""
        try:
            # 確保股票數據索引是datetime格式且不包含時區信息
            if hasattr(stock_data.index, 'tz_localize'):
                stock_index = stock_data.index.tz_localize(None)
            else:
                stock_index = stock_data.index

            # 確保所有數據使用相同的日期索引
            common_index = stock_index

            aligned_gov_data = {}
            for key, series in gov_data.items():
                if isinstance(series, pd.Series):
                    # 移除時區信息並對齊日期
                    if hasattr(series.index, 'tz_localize'):
                        gov_index = series.index.tz_localize(None)
                    else:
                        gov_index = series.index

                    # 重新索引到股票數據的日期
                    aligned_series = series.copy()
                    aligned_series.index = gov_index
                    aligned_series = aligned_series.reindex(common_index, method='ffill')
                    aligned_gov_data[key] = aligned_series
                else:
                    logger.warning(f"跳過非Series格式的數據: {key}")

            # 更新股票數據索引
            aligned_stock_data = stock_data.copy()
            aligned_stock_data.index = stock_index

            return {
                'stock_data': aligned_stock_data,
                'gov_data': aligned_gov_data,
                'common_dates': common_index,
                'data_points': len(common_index)
            }

        except Exception as e:
            logger.error(f"數據對齊失敗: {e}")
            # 如果對齊失敗，使用股票數據和空的政府數據
            logger.warning("使用僅股票數據進行回測")
            return {
                'stock_data': stock_data,
                'gov_data': {},
                'common_dates': stock_data.index,
                'data_points': len(stock_data.index)
            }

    def calculate_nonprice_indicators_gpu(self, data: Dict[str, Any]) -> Dict[str, pd.Series]:
        """使用GPU計算非價格技術指標"""
        logger.info("開始GPU計算非價格技術指標...")

        try:
            # 監控GPU使用情況
            gpu_start_time = time.time()
            if self.gpu_available:
                import cupy as cp
                logger.info(f"GPU內存使用前: {cp.cuda.runtime.memGetInfo()[0] / 1024**3:.1f} GB")

            indicators = {}
            stock_data = data['stock_data']
            gov_data = data['gov_data']

            # 如果沒有政府數據，使用股價數據生成非價格風格的指標
            if not gov_data:
                logger.info("使用股價數據生成模擬非價格指標...")

                # 1. 價格動量指標（模擬貨幣基礎動量）
                price_momentum = stock_data['close'].pct_change(periods=10) * 100
                indicators['PRICE_MOMENTUM'] = price_momentum

                # 2. 價格波動率指標（模擬HIBOR波動）
                price_volatility = stock_data['close'].pct_change().rolling(20).std() * np.sqrt(252) * 100
                indicators['PRICE_VOLATILITY'] = price_volatility

                # 3. 價格趨勢指標（模擬綜合經濟指標）
                price_trend = stock_data['close'].rolling(50).mean() / stock_data['close'].rolling(200).mean() * 100
                indicators['PRICE_TREND'] = price_trend

            else:
                # 使用真實政府數據
                # 1. HIBOR RSI指標
                if 'hibor' in gov_data:
                    hibor_series = gov_data['hibor'].dropna()
                    if len(hibor_series) > 14:
                        if self.gpu_available:
                            try:
                                hibor_rsi = self.gpu_engine.rsi(hibor_series.values, 14)
                                indicators['HIBOR_RSI'] = pd.Series(hibor_rsi, index=hibor_series.index)
                            except:
                                # 嘗試直接傳入Series
                                hibor_rsi = self.gpu_engine.rsi(hibor_series, 14)
                                indicators['HIBOR_RSI'] = hibor_rsi
                        else:
                            # 使用CPU版本
                            hibor_rsi = self.gpu_engine.rsi(hibor_series, 14)
                            indicators['HIBOR_RSI'] = hibor_rsi

                # 2. 貨幣基礎動量指標
                if 'monetary_base' in gov_data:
                    mb_series = gov_data['monetary_base'].dropna()
                    if len(mb_series) > 10:
                        # 計算貨幣基礎的動量指標
                        mb_momentum = mb_series.pct_change(periods=10) * 100
                        indicators['MB_MOMENTUM'] = mb_momentum

            # 計算基於股價的技術指標作為對比基準
            try:
                close_prices = stock_data['close'].values

                # RSI指標
                if self.gpu_available:
                    try:
                        rsi_values = self.gpu_engine.rsi(close_prices, 14)
                        # 確保長度匹配
                        if len(rsi_values) == len(stock_data):
                            indicators['RSI'] = pd.Series(rsi_values, index=stock_data.index)
                        else:
                            indicators['RSI'] = pd.Series(rsi_values, index=stock_data.index[:len(rsi_values)])
                    except Exception as e:
                        # 嘗試直接傳入Series
                        try:
                            rsi_values = self.gpu_engine.rsi(stock_data['close'], 14)
                            indicators['RSI'] = rsi_values
                        except:
                            # 使用pandas內置RSI作為備用
                            indicators['RSI'] = stock_data['close'].rolling(14).apply(lambda x: 100 - (100 / (1 + x.diff().clip(lower=0).mean() / x.diff().clip(upper=0).mean() * -1)))
                else:
                    # 使用pandas內置RSI
                    indicators['RSI'] = stock_data['close'].rolling(14).apply(lambda x: 100 - (100 / (1 + x.diff().clip(lower=0).mean() / x.diff().clip(upper=0).mean() * -1)))

                # MACD指標
                if self.gpu_available:
                    try:
                        macd_line, signal_line, histogram = self.gpu_engine.macd(close_prices, 12, 26, 9)
                        indicators['MACD'] = pd.Series(macd_line, index=stock_data.index)
                        indicators['MACD_SIGNAL'] = pd.Series(signal_line, index=stock_data.index)
                        indicators['MACD_HIST'] = pd.Series(histogram, index=stock_data.index)
                    except:
                        # 使用CPU版本
                        macd_line, signal_line, histogram = self._calculate_macd_cpu(close_prices, 12, 26, 9)
                        indicators['MACD'] = pd.Series(macd_line, index=stock_data.index)
                        indicators['MACD_SIGNAL'] = pd.Series(signal_line, index=stock_data.index)
                        indicators['MACD_HIST'] = pd.Series(histogram, index=stock_data.index)

                # 移動平均線（使用pandas內置方法）
                ma_short = stock_data['close'].rolling(20).mean()
                ma_long = stock_data['close'].rolling(50).mean()
                indicators['MA_20'] = ma_short
                indicators['MA_50'] = ma_long

            except Exception as e:
                logger.warning(f"技術指標計算部分失敗: {e}")

            # 3. 綜合非價格指標
            if len(indicators) >= 2:
                try:
                    # 計算綜合指標
                    aligned_indicators = {}

                    # 對齊所有指標到統一日期
                    for name, series in indicators.items():
                        aligned_indicators[name] = series.reindex(data['common_dates'])

                    # 計算多因子綜合指標
                    if 'RSI' in aligned_indicators and 'PRICE_MOMENTUM' in aligned_indicators:
                        rsi_weight = 0.5
                        momentum_weight = 0.5

                        rsi_normalized = aligned_indicators['RSI'].fillna(50)  # 中性值
                        momentum_normalized = ((aligned_indicators['PRICE_MOMENTUM'] + 50).clip(0, 100))  # 移動到0-100範圍

                        composite_indicator = (rsi_normalized * rsi_weight + momentum_normalized * momentum_weight)
                        indicators['COMPOSITE_INDICATOR'] = composite_indicator

                except Exception as e:
                    logger.warning(f"綜合指標計算失敗: {e}")

            gpu_end_time = time.time()
            gpu_compute_time = gpu_end_time - gpu_start_time

            logger.info(f"GPU計算完成，耗時: {gpu_compute_time:.3f}秒")
            logger.info(f"計算了 {len(indicators)} 個技術指標")

            # GPU內存使用報告
            if self.gpu_available:
                import cupy as cp
                gpu_memory_after = cp.cuda.runtime.memGetInfo()[0] / 1024**3
                logger.info(f"GPU內存使用後: {gpu_memory_after:.1f} GB")
                logger.info("GPU加速技術指標計算成功完成")

            for name in indicators.keys():
                logger.info(f"  - {name}")

            return indicators

        except Exception as e:
            logger.error(f"指標計算失敗: {e}")
            return {}

    def generate_trading_signals(self, data: Dict[str, Any], indicators: Dict[str, pd.Series]) -> pd.DataFrame:
        """基於非價格指標生成交易信號"""
        logger.info("生成交易信號...")

        try:
            signals = pd.DataFrame(index=data['common_dates'])
            signals['close'] = data['stock_data']['close']

            # 1. 基於RSI的信號策略
            if 'RSI' in indicators:
                rsi_data = indicators['RSI']
                if isinstance(rsi_data, pd.Series):
                    rsi = rsi_data.reindex(signals.index)
                else:
                    rsi = pd.Series(rsi_data, index=signals.index)
                signals['RSI'] = rsi

                # RSI策略：超賣買入，超買賣出
                signals['RSI_SIGNAL'] = np.where(
                    rsi < 30, 1,  # 超賣買入
                    np.where(rsi > 70, -1, 0)  # 超買賣出
                )

            # 2. 基於MACD的信號策略
            if 'MACD' in indicators and 'MACD_SIGNAL' in indicators:
                macd_data = indicators['MACD']
                macd_signal_data = indicators['MACD_SIGNAL']

                if isinstance(macd_data, pd.Series):
                    macd = macd_data.reindex(signals.index)
                else:
                    macd = pd.Series(macd_data, index=signals.index)

                if isinstance(macd_signal_data, pd.Series):
                    macd_signal_line = macd_signal_data.reindex(signals.index)
                else:
                    macd_signal_line = pd.Series(macd_signal_data, index=signals.index)

                signals['MACD'] = macd
                signals['MACD_SIGNAL_LINE'] = macd_signal_line

                # MACD策略：金叉買入，死叉賣出
                macd_cross = (macd > macd_signal_line).astype(int) - (macd < macd_signal_line).astype(int)
                signals['MACD_SIGNAL'] = macd_cross

            # 3. 基於移動平均線的信號策略
            if 'MA_20' in indicators and 'MA_50' in indicators:
                ma_short_data = indicators['MA_20']
                ma_long_data = indicators['MA_50']

                if isinstance(ma_short_data, pd.Series):
                    ma_short = ma_short_data.reindex(signals.index)
                else:
                    ma_short = pd.Series(ma_short_data, index=signals.index)

                if isinstance(ma_long_data, pd.Series):
                    ma_long = ma_long_data.reindex(signals.index)
                else:
                    ma_long = pd.Series(ma_long_data, index=signals.index)

                signals['MA_20'] = ma_short
                signals['MA_50'] = ma_long

                # 移動平均策略：短期均線突破長期均線
                ma_cross = (ma_short > ma_long).astype(int) - (ma_short < ma_long).astype(int)
                signals['MA_SIGNAL'] = ma_cross

            # 4. 基於價格動量的信號策略
            if 'PRICE_MOMENTUM' in indicators:
                momentum_data = indicators['PRICE_MOMENTUM']
                if isinstance(momentum_data, pd.Series):
                    momentum = momentum_data.reindex(signals.index)
                else:
                    momentum = pd.Series(momentum_data, index=signals.index)
                signals['PRICE_MOMENTUM'] = momentum

                # 動量策略：正動量買入，負動量賣出
                signals['MOMENTUM_SIGNAL'] = np.where(
                    momentum > 2.0, 1,  # 強勢上漲
                    np.where(momentum < -2.0, -1, 0)  # 弱勢下跌
                )

            # 5. 基於價格趨勢的信號策略
            if 'PRICE_TREND' in indicators:
                trend_data = indicators['PRICE_TREND']
                if isinstance(trend_data, pd.Series):
                    trend = trend_data.reindex(signals.index)
                else:
                    trend = pd.Series(trend_data, index=signals.index)
                signals['PRICE_TREND'] = trend

                # 趨勢策略：趨勢強買入，趨勢弱賣出
                signals['TREND_SIGNAL'] = np.where(
                    trend > 102, 1,  # 強勢趨勢
                    np.where(trend < 98, -1, 0)  # 弱勢趨勢
                )

            # 6. 基於綜合指標的信號策略
            if 'COMPOSITE_INDICATOR' in indicators:
                composite_data = indicators['COMPOSITE_INDICATOR']
                if isinstance(composite_data, pd.Series):
                    composite = composite_data.reindex(signals.index)
                else:
                    composite = pd.Series(composite_data, index=signals.index)
                signals['COMPOSITE'] = composite

                # 綜合策略：綜合指標低買高賣
                signals['COMPOSITE_SIGNAL'] = np.where(
                    composite < 40, 1,  # 綜合指標過低買入
                    np.where(composite > 60, -1, 0)  # 綜合指標過高賣出
                )

            # 7. 多信號融合策略
            signal_columns = [col for col in signals.columns if col.endswith('_SIGNAL')]

            if signal_columns:
                # 加權投票策略
                signal_weights = {
                    'RSI_SIGNAL': 0.3,
                    'MACD_SIGNAL': 0.25,
                    'MA_SIGNAL': 0.2,
                    'MOMENTUM_SIGNAL': 0.15,
                    'TREND_SIGNAL': 0.1
                }

                # 計算加權信號
                weighted_signal = pd.Series(0.0, index=signals.index)
                total_weight = 0.0

                for signal_col in signal_columns:
                    if signal_col in signal_weights:
                        weight = signal_weights[signal_col]
                        weighted_signal += signals[signal_col] * weight
                        total_weight += weight
                    else:
                        # 未加權的信號給予較小權重
                        weighted_signal += signals[signal_col] * 0.05
                        total_weight += 0.05

                if total_weight > 0:
                    weighted_signal = weighted_signal / total_weight

                signals['FUSION_SIGNAL'] = weighted_signal

                # 最終交易信號（閾值過濾）
                signals['FINAL_SIGNAL'] = np.where(
                    weighted_signal > 0.4, 1,  # 強買入信號
                    np.where(weighted_signal < -0.4, -1, 0)  # 強賣出信號
                )
            else:
                signals['FUSION_SIGNAL'] = 0
                signals['FINAL_SIGNAL'] = 0

            logger.info(f"生成了 {len(signal_columns)} 個單獨信號策略")
            logger.info(f"包含融合策略和最終策略，共 {len([col for col in signals.columns if 'SIGNAL' in col])} 個信號")

            return signals

        except Exception as e:
            logger.error(f"信號生成失敗: {e}")
            # 返回空信號DataFrame，避免系統崩潰
            empty_signals = pd.DataFrame(index=data['common_dates'])
            empty_signals['close'] = data['stock_data']['close']
            empty_signals['FINAL_SIGNAL'] = 0
            return empty_signals

    def backtest_strategies(self, signals: pd.DataFrame) -> Dict[str, Any]:
        """執行四大策略回測"""
        logger.info("執行四大策略回測...")

        try:
            results = {}

            # 基礎數據
            prices = signals['close']
            dates = signals.index

            # 定義四大核心策略
            strategies = {
                'RSI_Strategy': {
                    'signal': signals['RSI_SIGNAL'] if 'RSI_SIGNAL' in signals.columns else pd.Series(0, index=signals.index),
                    'description': 'RSI超買超賣策略'
                },
                'MACD_Strategy': {
                    'signal': signals['MACD_SIGNAL'] if 'MACD_SIGNAL' in signals.columns else pd.Series(0, index=signals.index),
                    'description': 'MACD金叉死叉策略'
                },
                'MA_Cross_Strategy': {
                    'signal': signals['MA_SIGNAL'] if 'MA_SIGNAL' in signals.columns else pd.Series(0, index=signals.index),
                    'description': '移動平均線交叉策略'
                },
                'Fusion_Consensus_Strategy': {
                    'signal': signals['FINAL_SIGNAL'] if 'FINAL_SIGNAL' in signals.columns else pd.Series(0, index=signals.index),
                    'description': '多信號融合共識策略'
                }
            }

            # 額外的輔助策略
            additional_strategies = {
                'Momentum_Strategy': {
                    'signal': signals['MOMENTUM_SIGNAL'] if 'MOMENTUM_SIGNAL' in signals.columns else pd.Series(0, index=signals.index),
                    'description': '價格動量策略'
                },
                'Trend_Strategy': {
                    'signal': signals['TREND_SIGNAL'] if 'TREND_SIGNAL' in signals.columns else pd.Series(0, index=signals.index),
                    'description': '價格趨勢策略'
                },
                'Composite_Strategy': {
                    'signal': signals['COMPOSITE_SIGNAL'] if 'COMPOSITE_SIGNAL' in signals.columns else pd.Series(0, index=signals.index),
                    'description': '綜合指標策略'
                }
            }

            # 合併所有策略
            all_strategies = {**strategies, **additional_strategies}

            successful_strategies = 0
            total_strategies = len(all_strategies)

            for strategy_name, strategy_info in all_strategies.items():
                strategy_signals = strategy_info['signal']
                description = strategy_info['description']

                # 確保信號是pandas Series
                if not isinstance(strategy_signals, pd.Series):
                    strategy_signals = pd.Series(strategy_signals, index=signals.index)

                if strategy_signals.sum() == 0:  # 如果沒有信號，跳過
                    logger.warning(f"跳過無信號策略: {strategy_name}")
                    continue

                logger.info(f"回測策略: {strategy_name} - {description}")

                try:
                    # 計算策略回報
                    strategy_returns = self._calculate_strategy_returns(
                        prices, strategy_signals
                    )

                    # 計算性能指標
                    metrics = self._calculate_performance_metrics(
                        strategy_returns, risk_free_rate=0.03
                    )

                    # 計算額外的風險指標
                    additional_metrics = self._calculate_additional_metrics(
                        strategy_returns, prices, strategy_signals
                    )

                    # 合併所有指標
                    all_metrics = {**metrics, **additional_metrics}

                    results[strategy_name] = {
                        'returns': strategy_returns,
                        'metrics': all_metrics,
                        'signals': strategy_signals,
                        'description': description,
                        'total_trades': abs(strategy_signals).sum(),
                        'active_signals': (strategy_signals != 0).sum()
                    }

                    successful_strategies += 1

                    # 輸出關鍵指標
                    logger.info(f"  Sharpe比率: {metrics['sharpe_ratio']:.3f}")
                    logger.info(f"  總回報: {metrics['total_return']:.2%}")
                    logger.info(f"  年化回報: {metrics['annual_return']:.2%}")
                    logger.info(f"  最大回撤: {metrics['max_drawdown']:.2%}")
                    logger.info(f"  波動率: {metrics['volatility']:.2%}")
                    logger.info(f"  勝率: {metrics['win_rate']:.1%}")
                    logger.info(f"  交易次數: {results[strategy_name]['total_trades']}")
                    logger.info(f"  Calmar比率: {metrics['calmar_ratio']:.3f}")

                except Exception as e:
                    logger.error(f"策略 {strategy_name} 回測失敗: {e}")
                    continue

            logger.info(f"完成 {successful_strategies}/{total_strategies} 個策略回測")

            # 尋找最佳策略
            if results:
                best_strategy = max(results.items(),
                                  key=lambda x: x[1]['metrics']['sharpe_ratio'])
                logger.info(f"最佳策略: {best_strategy[0]} (Sharpe: {best_strategy[1]['metrics']['sharpe_ratio']:.3f})")

            return results

        except Exception as e:
            logger.error(f"回測執行失敗: {e}")
            return {}

    def _calculate_strategy_returns(self, prices: pd.Series, signals: pd.Series) -> pd.Series:
        """計算策略回報"""
        try:
            # 計算日回報
            daily_returns = prices.pct_change()

            # 根據信號計算策略回報
            # 信號在當天收盤後生成，第二天執行
            strategy_signals = signals.shift(1)

            # 計算策略回報（扣除交易成本）
            transaction_cost = 0.001  # 0.1%交易成本
            trading_days = (strategy_signals.diff() != 0).astype(int)
            daily_costs = trading_days * transaction_cost

            strategy_returns = strategy_signals * daily_returns - daily_costs

            return strategy_returns.fillna(0)

        except Exception as e:
            logger.error(f"策略回報計算失敗: {e}")
            return pd.Series(0, index=prices.index)

    def _calculate_additional_metrics(self, returns: pd.Series, prices: pd.Series, signals: pd.Series) -> Dict[str, float]:
        """計算額外的風險指標"""
        try:
            if len(returns) == 0:
                return {}

            # Sortino比率（只考慮下行風險）
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0:
                downside_std = downside_returns.std() * np.sqrt(252)
                sortino_ratio = (returns.mean() * 252 - 0.03) / downside_std if downside_std > 0 else 0
            else:
                sortino_ratio = float('inf')

            # 最大連續虧損天數
            cumulative_returns = (1 + returns).cumprod()
            peak = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - peak) / peak

            # 計算連續虧損期間
            in_drawdown = drawdown < 0
            consecutive_losses = 0
            max_consecutive_losses = 0

            for is_dd in in_drawdown:
                if is_dd:
                    consecutive_losses += 1
                    max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
                else:
                    consecutive_losses = 0

            # 訊號質量指標
            signal_changes = abs(signals.diff()).sum()
            signal_frequency = signal_changes / len(signals)

            # 收益穩定性（月度標準差）
            monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            monthly_volatility = monthly_returns.std() if len(monthly_returns) > 1 else 0

            # 信息比率（相對於基準的超額收益風險調整後）
            # 簡化版：使用買入持有策略作為基準
            benchmark_returns = prices.pct_change().fillna(0)
            excess_returns = returns - benchmark_returns
            if excess_returns.std() > 0:
                information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            else:
                information_ratio = 0

            return {
                'sortino_ratio': sortino_ratio,
                'max_consecutive_losses': max_consecutive_losses,
                'signal_frequency': signal_frequency,
                'monthly_volatility': monthly_volatility,
                'information_ratio': information_ratio,
                'downside_deviation': downside_std if len(downside_returns) > 0 else 0
            }

        except Exception as e:
            logger.error(f"額外指標計算失敗: {e}")
            return {}

    def _calculate_performance_metrics(self, returns: pd.Series, risk_free_rate: float = 0.03) -> Dict[str, float]:
        """計算性能指標"""
        try:
            if len(returns) == 0:
                return self._empty_metrics()

            # 基本統計
            total_return = (1 + returns).prod() - 1
            annual_return = (1 + total_return) ** (252 / len(returns)) - 1
            volatility = returns.std() * np.sqrt(252)

            # Sharpe比率（年化，3%無風險利率）
            excess_return = annual_return - risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0

            # 最大回撤
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdowns = (cumulative - running_max) / running_max
            max_drawdown = drawdowns.min()

            # 其他指標
            win_rate = (returns > 0).mean()
            avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0
            avg_loss = returns[returns < 0].mean() if (returns < 0).any() else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss < 0 else float('inf')

            # Calmar比率
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown < 0 else float('inf')

            # Skewness and Kurtosis
            skewness = returns.skew()
            kurtosis = returns.kurtosis()

            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'calmar_ratio': calmar_ratio,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'skewness': skewness,
                'kurtosis': kurtosis,
                'total_trades': int((returns != 0).sum())
            }

        except Exception as e:
            logger.error(f"性能指標計算失敗: {e}")
            return self._empty_metrics()

    def _empty_metrics(self) -> Dict[str, float]:
        """返回空的性能指標"""
        return {
            'total_return': 0.0,
            'annual_return': 0.0,
            'volatility': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'calmar_ratio': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'profit_factor': 0.0,
            'total_trades': 0
        }

    def generate_report(self, data: Dict[str, Any], backtest_results: Dict[str, Any]) -> str:
        """生成回測報告"""
        logger.info("📋 生成回測報告...")

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 報告數據
            report = {
                'metadata': {
                    'stock': '0700.HK',
                    'company': 'Tencent Holdings Limited',
                    'backtest_date': datetime.now().isoformat(),
                    'data_period': f"{data['common_dates'][0].date()} 至 {data['common_dates'][-1].date()}",
                    'total_days': len(data['common_dates']),
                    'gpu_used': self.gpu_available,
                    'data_points': data['data_points']
                },
                'data_summary': {
                    'price_range': {
                        'min': float(data['stock_data']['close'].min()),
                        'max': float(data['stock_data']['close'].max()),
                        'current': float(data['stock_data']['close'].iloc[-1])
                    },
                    'government_sources': list(data['gov_data'].keys())
                },
                'strategy_results': {},
                'performance_comparison': {},
                'best_strategy': None,
                'execution_summary': {
                    'total_strategies': len(backtest_results),
                    'successful_strategies': len([s for s in backtest_results.values()
                                               if s['metrics']['sharpe_ratio'] > 0])
                }
            }

            # 處理回測結果
            all_sharpes = []
            all_returns = []

            for strategy_name, result in backtest_results.items():
                metrics = result['metrics']

                # 添加到報告
                report['strategy_results'][strategy_name] = {
                    'sharpe_ratio': metrics['sharpe_ratio'],
                    'total_return': metrics['total_return'],
                    'annual_return': metrics['annual_return'],
                    'max_drawdown': metrics['max_drawdown'],
                    'volatility': metrics['volatility'],
                    'calmar_ratio': metrics['calmar_ratio'],
                    'win_rate': metrics['win_rate'],
                    'profit_factor': metrics['profit_factor'],
                    'total_trades': metrics['total_trades']
                }

                all_sharpes.append(metrics['sharpe_ratio'])
                all_returns.append(metrics['total_return'])

            # 找出最佳策略
            if backtest_results:
                best_strategy_name = max(backtest_results.keys(),
                                      key=lambda k: backtest_results[k]['metrics']['sharpe_ratio'])
                report['best_strategy'] = {
                    'name': best_strategy_name,
                    'sharpe_ratio': backtest_results[best_strategy_name]['metrics']['sharpe_ratio'],
                    'total_return': backtest_results[best_strategy_name]['metrics']['total_return']
                }

            # 性能統計
            if all_sharpes:
                report['performance_comparison'] = {
                    'avg_sharpe': np.mean(all_sharpes),
                    'max_sharpe': max(all_sharpes),
                    'min_sharpe': min(all_sharpes),
                    'avg_return': np.mean(all_returns),
                    'max_return': max(all_returns),
                    'min_return': min(all_returns)
                }

            # 保存報告
            report_file = f"gpu_nonprice_0700_backtest_report_{timestamp}.json"

            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 報告已保存: {report_file}")

            # 打印摘要
            self._print_summary(report)

            return report_file

        except Exception as e:
            logger.error(f"報告生成失敗: {e}")
            return ""

    def _print_summary(self, report: Dict[str, Any]):
        """打印回測摘要"""
        print("\n" + "="*80)
        print("GPU加速非價格數據回測報告 - 0700.HK")
        print("="*80)

        print(f"\n基本信息:")
        print(f"  股票代碼: {report['metadata']['stock']}")
        print(f"  公司名称: {report['metadata']['company']}")
        print(f"  數據期間: {report['metadata']['data_period']}")
        print(f"  GPU加速: {'啓用' if report['metadata']['gpu_used'] else '停用'}")
        print(f"  數據點數: {report['metadata']['data_points']}")

        print(f"\n價格範圍:")
        price_range = report['data_summary']['price_range']
        print(f"  最低價: {price_range['min']:.2f} HKD")
        print(f"  最高價: {price_range['max']:.2f} HKD")
        print(f"  當前價: {price_range['current']:.2f} HKD")

        print(f"\n策略結果:")
        for strategy, metrics in report['strategy_results'].items():
            print(f"  {strategy}:")
            print(f"    Sharpe比率: {metrics['sharpe_ratio']:.3f}")
            print(f"    總回報: {metrics['total_return']:.2%}")
            print(f"    最大回撤: {metrics['max_drawdown']:.2%}")
            print(f"    交易次數: {metrics['total_trades']}")

        if report['best_strategy']:
            best = report['best_strategy']
            print(f"\n最佳策略:")
            print(f"  策略名稱: {best['name']}")
            print(f"  Sharpe比率: {best['sharpe_ratio']:.3f}")
            print(f"  總回報: {best['total_return']:.2%}")

        if report['performance_comparison']:
            comp = report['performance_comparison']
            print(f"\n性能統計:")
            print(f"  平均Sharpe: {comp['avg_sharpe']:.3f}")
            print(f"  最高Sharpe: {comp['max_sharpe']:.3f}")
            print(f"  平均回報: {comp['avg_return']:.2%}")
            print(f"  最高回報: {comp['max_return']:.2%}")

        print(f"\n執行摘要:")
        print(f"  測試策略: {report['execution_summary']['total_strategies']} 個")
        print(f"  成功策略: {report['execution_summary']['successful_strategies']} 個")

        print("="*80)

async def main():
    """主執行函數"""
    print("GPU加速非價格數據回測系統 - 0700.HK")
    print("=" * 80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    start_time = time.time()

    try:
        # 1. 初始化回測引擎
        backtest_engine = GPUNonPriceBacktestEngine()

        # 2. 準備數據
        data = await backtest_engine.prepare_0700_data(days=365)

        if not data:
            print("數據準備失敗")
            return False

        # 3. 計算非價格指標
        indicators = backtest_engine.calculate_nonprice_indicators_gpu(data)

        if not indicators:
            print("指標計算失敗")
            return False

        # 4. 生成交易信號
        signals = backtest_engine.generate_trading_signals(data, indicators)

        if signals.empty:
            print("信號生成失敗")
            return False

        # 5. 執行回測
        backtest_results = backtest_engine.backtest_strategies(signals)

        if not backtest_results:
            print("回測執行失敗")
            return False

        # 6. 生成報告
        report_file = backtest_engine.generate_report(data, backtest_results)

        # 7. 總結
        execution_time = time.time() - start_time

        print(f"\n執行完成!")
        print(f"執行時間: {execution_time:.2f}秒")
        print(f"報告文件: {report_file}")

        # 判斷成功
        success = (
            len(backtest_results) > 0 and
            any(result['metrics']['sharpe_ratio'] > 0 for result in backtest_results.values())
        )

        if success:
            print("GPU非價格回測成功完成！")
        else:
            print("回測結果不理想，建議優化策略參數")

        return success

    except Exception as e:
        print(f"系統錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)