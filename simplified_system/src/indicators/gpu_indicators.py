#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
GPU加速技術指標計算模塊
使用新的GPU計算核心實現高性能向量化技術指標計算
解決過度CPU回退問題，實現真正的GPU加速
"""

import logging
import os
import sys
from typing import Dict, Union

import numpy as np
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from src.gpu.gpu_computation_core import get_gpu_computation_core

from utils.gpu_detector import get_gpu_environment

logger = logging.getLogger(__name__)


class GPUTechnicalIndicators:
    """GPU加速技術指標計算類 - 使用新的GPU計算核心"""

    def __init__(self, use_gpu: bool = True, gpu_device: int = 0):
        """
        初始化GPU技術指標計算器

        Args:
            use_gpu: 是否使用GPU加速（默認為True）
            gpu_device: GPU设备ID
        """
        self.gpu_env = get_gpu_environment()
        self.use_gpu = use_gpu and self.gpu_env.is_gpu_available()
        self.gpu_device = gpu_device
        self.backend = "gpu" if self.use_gpu else "cpu"

        # 初始化新的GPU计算核心
        if self.use_gpu:
            try:
                self.gpu_core = get_gpu_computation_core(gpu_device)
                logger.info(
                    f"GPU Technical Indicators initialized with new GPU core on device {gpu_device}"
                )
            except Exception as e:
                logger.error(
                    f"GPU core initialization failed: {e}, falling back to CPU"
                )
                self.use_gpu = False
                self.backend = "cpu"
                self.gpu_core = None
        else:
            self.gpu_core = None

        logger.info(
            f"GPU Technical Indicators initialized with backend: {self.backend}"
        )

    def _to_gpu(self, data: np.ndarray) -> Union[np.ndarray, "cp.ndarray"]:
        """將數據轉移到GPU"""
        if self.use_gpu and self.cp is not None:
            return self.cp.asarray(data)
        return data

    def _to_cpu(self, data: Union[np.ndarray, "cp.ndarray"]) -> np.ndarray:
        """將數據從GPU轉移到CPU"""
        if self.use_gpu and self.cp is not None and hasattr(data, "get"):
            return data.get()
        return data

    def rsi(self, prices: Union[np.ndarray, pd.Series], period: int = 14) -> np.ndarray:
        """
        計算RSI指標（新的GPU加速版本）

        Args:
            prices: 價格數據
            period: RSI週期

        Returns:
            RSI值數組
        """
        if isinstance(prices, pd.Series):
            prices = prices.values.astype(np.float32)
        else:
            prices = prices.astype(np.float32)

        if self.use_gpu and self.gpu_core is not None:
            try:
                rsi_gpu = self.gpu_core.calculate_rsi_gpu(prices, period)
                # 将结果移回CPU
                if hasattr(rsi_gpu, "get"):
                    return rsi_gpu.get()
                else:
                    return np.array(rsi_gpu)
            except Exception as e:
                logger.error(
                    f"GPU core RSI calculation failed: {e}, falling back to CPU"
                )
                return self._rsi_cpu(prices, period)
        else:
            return self._rsi_cpu(prices, period)

    def _rsi_cpu(self, prices: np.ndarray, period: int) -> np.ndarray:
        """CPU版本的RSI計算（回退）"""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window = period).mean()
        avg_loss = pd.Series(loss).rolling(window = period).mean()

        rs = avg_gain / np.where(avg_loss == 0, 1e - 10, avg_loss)
        rsi = 100 - (100 / (1 + rs))

        return rsi.values

    def macd(
        self,
        prices: Union[np.ndarray, pd.Series],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> Dict[str, np.ndarray]:
        """
        計算MACD指標（新的GPU加速版本）

        Args:
            prices: 價格數據
            fast: 快線週期
            slow: 慢線週期
            signal: 信號線週期

        Returns:
            包含MACD, SIGNAL, HIST的字典
        """
        if isinstance(prices, pd.Series):
            prices = prices.values.astype(np.float32)
        else:
            prices = prices.astype(np.float32)

        if self.use_gpu and self.gpu_core is not None:
            try:
                macd_gpu, signal_gpu, hist_gpu = self.gpu_core.calculate_macd_gpu(
                    prices, fast, slow, signal
                )
                return {
                    "MACD": (
                        macd_gpu.get()
                        if hasattr(macd_gpu, "get")
                        else np.array(macd_gpu)
                    ),
                    "SIGNAL": (
                        signal_gpu.get()
                        if hasattr(signal_gpu, "get")
                        else np.array(signal_gpu)
                    ),
                    "HIST": (
                        hist_gpu.get()
                        if hasattr(hist_gpu, "get")
                        else np.array(hist_gpu)
                    ),
                }
            except Exception as e:
                logger.error(
                    f"GPU core MACD calculation failed: {e}, falling back to CPU"
                )
                return self._macd_cpu(prices, fast, slow, signal)
        else:
            return self._macd_cpu(prices, fast, slow, signal)

    def _macd_cpu(
        self, prices: np.ndarray, fast: int, slow: int, signal: int
    ) -> Dict[str, np.ndarray]:
        """CPU版本的MACD計算（回退）"""
        prices_series = pd.Series(prices)
        ema_fast = prices_series.ewm(span = fast).mean()
        ema_slow = prices_series.ewm(span = slow).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span = signal).mean()
        histogram = macd_line - signal_line

        return {
            "MACD": macd_line.values,
            "SIGNAL": signal_line.values,
            "HIST": histogram.values,
        }

    def bollinger_bands(
        self,
        prices: Union[np.ndarray, pd.Series],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Dict[str, np.ndarray]:
        """
        計算布林帶指標（GPU加速版本）

        Args:
            prices: 價格數據
            period: 週期
            std_dev: 標準差倍數

        Returns:
            包含上軌、中軌、下軌的字典
        """
        if isinstance(prices, pd.Series):
            prices = prices.values

        if self.use_gpu:
            return self._bollinger_bands_gpu(prices, period, std_dev)
        else:
            return self._bollinger_bands_cpu(prices, period, std_dev)

    def _bollinger_bands_gpu(
        self, prices: np.ndarray, period: int, std_dev: float
    ) -> Dict[str, np.ndarray]:
        """GPU版本的布林帶計算"""
        try:
            prices_gpu = self._to_gpu(prices)

            # 計算移動平均
            kernel = self.cp.ones(period) / period
            middle_band = self.cp.convolve(prices_gpu, kernel, mode="valid")

            # 填充前面的NaN值
            middle_band = self.cp.concatenate(
                [self.cp.full(period - 1, self.cp.nan), middle_band]
            )

            # 計算標準差
            rolling_std = self.cp.zeros_like(prices_gpu)
            for i in range(period - 1, len(prices_gpu)):
                window = prices_gpu[i - period + 1 : i + 1]
                rolling_std[i] = self.cp.std(window)

            # 計算上下軌
            upper_band = middle_band + (rolling_std * std_dev)
            lower_band = middle_band - (rolling_std * std_dev)

            return {
                "UPPER": self._to_cpu(upper_band),
                "MIDDLE": self._to_cpu(middle_band),
                "LOWER": self._to_cpu(lower_band),
            }

        except Exception as e:
            logger.warning(
                f"GPU Bollinger Bands calculation failed, falling back to CPU: {e}"
            )
            return self._bollinger_bands_cpu(prices, period, std_dev)

    def _bollinger_bands_cpu(
        self, prices: np.ndarray, period: int, std_dev: float
    ) -> Dict[str, np.ndarray]:
        """CPU版本的布林帶計算（回退）"""
        prices_series = pd.Series(prices)
        middle_band = prices_series.rolling(window = period).mean()
        rolling_std = prices_series.rolling(window = period).std()

        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)

        return {
            "UPPER": upper_band.values,
            "MIDDLE": middle_band.values,
            "LOWER": lower_band.values,
        }

    def calculate_multiple_indicators(
        self, prices: Union[np.ndarray, pd.Series], indicators_config: Dict[str, Dict]
    ) -> Dict[str, np.ndarray]:
        """
        批量計算多個技術指標

        Args:
            prices: 價格數據
            indicators_config: 指標配置字典
                {
                    'rsi': {'period': 14},
                    'macd': {'fast': 12, 'slow': 26, 'signal': 9},
                    'bollinger': {'period': 20, 'std_dev': 2.0}
                }

        Returns:
            所有指標結果的字典
        """
        results = {}

        if "rsi" in indicators_config:
            config = indicators_config["rsi"]
            period = config.get("period", 14)
            results["RSI"] = self.rsi(prices, period)

        if "macd" in indicators_config:
            config = indicators_config["macd"]
            fast = config.get("fast", 12)
            slow = config.get("slow", 26)
            signal = config.get("signal", 9)
            macd_results = self.macd(prices, fast, slow, signal)
            results.update(macd_results)

        if "sma" in indicators_config:
            config = indicators_config["sma"]
            period = config.get("period", 20)
            results["SMA"] = self.moving_average(prices, period, "sma")

        if "ema" in indicators_config:
            config = indicators_config["ema"]
            period = config.get("period", 20)
            results["EMA"] = self.moving_average(prices, period, "ema")

        if "kdj" in indicators_config:
            config = indicators_config["kdj"]
            k_period = config.get("k_period", 9)
            d_period = config.get("d_period", 3)
            # 需要OHLC数据，这里简化处理
            if hasattr(prices, "__len__") and len(prices.shape) == 1:
                # 如果只有close价格，使用close模拟high / low
                kdj_results = self.kdj(
                    prices, prices * 1.01, prices * 0.99, k_period, d_period
                )
                results.update(
                    {
                        "KDJ_K": kdj_results["K"],
                        "KDJ_D": kdj_results["D"],
                        "KDJ_J": kdj_results["J"],
                    }
                )

        if "bollinger" in indicators_config:
            config = indicators_config["bollinger"]
            period = config.get("period", 20)
            std_dev = config.get("std_dev", 2.0)
            bb_results = self.bollinger_bands(prices, period, std_dev)
            results.update(
                {
                    "BB_UPPER": bb_results["UPPER"],
                    "BB_MIDDLE": bb_results["MIDDLE"],
                    "BB_LOWER": bb_results["LOWER"],
                }
            )

        return results

    def moving_average(
        self,
        prices: Union[np.ndarray, pd.Series],
        period: int = 20,
        ma_type: str = "sma",
    ) -> np.ndarray:
        """
        計算移動平均指標（GPU加速版本）

        Args:
            prices: 價格數據
            period: 週期
            ma_type: 移動平均類型 ('sma' 或 'ema')

        Returns:
            移動平均值數組
        """
        if isinstance(prices, pd.Series):
            prices = prices.values.astype(np.float32)
        else:
            prices = prices.astype(np.float32)

        if self.use_gpu and self.gpu_core is not None:
            try:
                ma_gpu = self.gpu_core.calculate_moving_average_gpu(
                    prices, period, ma_type
                )
                return ma_gpu.get() if hasattr(ma_gpu, "get") else np.array(ma_gpu)
            except Exception as e:
                logger.error(
                    f"GPU core moving average calculation failed: {e}, falling back to CPU"
                )
                return self._moving_average_cpu(prices, period, ma_type)
        else:
            return self._moving_average_cpu(prices, period, ma_type)

    def _moving_average_cpu(
        self, prices: np.ndarray, period: int, ma_type: str
    ) -> np.ndarray:
        """CPU版本的移動平均計算"""
        if ma_type.lower() == "sma":
            return (
                pd.Series(prices)
                .rolling(window = period)
                .mean()
                .fillna(method="bfill")
                .values
            )
        elif ma_type.lower() == "ema":
            return pd.Series(prices).ewm(span = period).mean().values
        else:
            raise ValueError(f"Unsupported moving average type: {ma_type}")

    def kdj(
        self,
        close: Union[np.ndarray, pd.Series],
        high: Union[np.ndarray, pd.Series],
        low: Union[np.ndarray, pd.Series],
        k_period: int = 9,
        d_period: int = 3,
    ) -> Dict[str, np.ndarray]:
        """
        計算KDJ指標（GPU加速版本）

        Args:
            close: 收盤價數據
            high: 最高價數據
            low: 最低價數據
            k_period: K值週期
            d_period: D值週期

        Returns:
            包含K, D, J的字典
        """
        # 确保数据为numpy数组
        if isinstance(close, pd.Series):
            close = close.values.astype(np.float32)
        else:
            close = close.astype(np.float32)

        if isinstance(high, pd.Series):
            high = high.values.astype(np.float32)
        else:
            high = high.astype(np.float32)

        if isinstance(low, pd.Series):
            low = low.values.astype(np.float32)
        else:
            low = low.astype(np.float32)

        if self.use_gpu and self.gpu_core is not None:
            try:
                k_gpu, d_gpu, j_gpu = self.gpu_core.calculate_kdj_gpu(
                    high, low, close, k_period, d_period
                )
                return {
                    "K": k_gpu.get() if hasattr(k_gpu, "get") else np.array(k_gpu),
                    "D": d_gpu.get() if hasattr(d_gpu, "get") else np.array(d_gpu),
                    "J": j_gpu.get() if hasattr(j_gpu, "get") else np.array(j_gpu),
                }
            except Exception as e:
                logger.error(
                    f"GPU core KDJ calculation failed: {e}, falling back to CPU"
                )
                return self._kdj_cpu(close, high, low, k_period, d_period)
        else:
            return self._kdj_cpu(close, high, low, k_period, d_period)

    def _kdj_cpu(
        self,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        k_period: int,
        d_period: int,
    ) -> Dict[str, np.ndarray]:
        """CPU版本的KDJ計算"""

        def rsv_ema(data, period):
            alpha = 2 / (period + 1)
            ema = np.zeros_like(data, dtype = np.float32)
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
            return ema

        # 计算RSV
        lowest_low = np.array(
            [np.min(low[max(0, i - k_period + 1) : i + 1]) for i in range(len(low))]
        )
        highest_high = np.array(
            [np.max(high[max(0, i - k_period + 1) : i + 1]) for i in range(len(high))]
        )

        rsv = np.where(
            highest_high == lowest_low,
            50.0,
            100 * (close - lowest_low) / (highest_high - lowest_low),
        )

        # K, D, J计算
        k_values = rsv_ema(rsv, d_period)
        d_values = rsv_ema(k_values, d_period)
        j_values = 3 * k_values - 2 * d_values

        return {"K": k_values, "D": d_values, "J": j_values}

    def get_backend_info(self) -> Dict[str, any]:
        """獲取後端信息"""
        return {
            "backend": self.backend,
            "use_gpu": self.use_gpu,
            "gpu_available": self.gpu_env.is_gpu_available(),
            "gpu_info": self.gpu_env.get_system_info() if self.use_gpu else None,
        }
