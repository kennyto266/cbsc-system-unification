#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VectorBT GPU集成模組
VectorBT GPU Integration Module

為VectorBT回測引擎提供安全的GPU加速支持
Provides secure GPU acceleration support for VectorBT backtesting engine
"""

import logging
import time
import warnings
from typing import Dict, Any, Optional, List, Tuple, Union
import numpy as np
import pandas as pd
from pathlib import Path

# 安全導入依賴
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    cp = None
    GPU_AVAILABLE = False

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    vbt = None
    VECTORBT_AVAILABLE = False

from .gpu_acceleration_support import get_gpu_acceleration_manager
from src.utils.dependency_manager import DependencyManager

logger = logging.getLogger(__name__)

class VectorBTGPUIntegration:
    """VectorBT GPU集成器"""

    def __init__(self, auto_detect_gpu: bool = True):
        self.auto_detect_gpu = auto_detect_gpu
        self.gpu_manager = None
        self.initialized = False
        self.dependency_manager = DependencyManager()

        # 初始化
        if auto_detect_gpu:
            self._initialize()

    def _initialize(self):
        """初始化GPU集成"""
        try:
            if not VECTORBT_AVAILABLE:
                logger.warning("VectorBT不可用，GPU集成功能受限")
                return False

            if not GPU_AVAILABLE:
                logger.warning("CuPy不可用，無法使用GPU加速")
                return False

            # 初始化GPU管理器
            self.gpu_manager = get_gpu_acceleration_manager()
            if not self.gpu_manager.initialize():
                logger.warning("GPU管理器初始化失敗")
                return False

            self.initialized = True
            logger.info("VectorBT GPU集成初始化成功")
            return True

        except Exception as e:
            logger.error(f"VectorBT GPU集成初始化失敗: {e}")
            return False

    def is_gpu_enabled(self) -> bool:
        """檢查GPU是否啟用"""
        return self.initialized and self.gpu_manager and self.gpu_manager.gpu_enabled

    def get_acceleration_status(self) -> Dict[str, Any]:
        """獲取加速狀態"""
        status = {
            "vectorbt_available": VECTORBT_AVAILABLE,
            "gpu_available": GPU_AVAILABLE,
            "integration_initialized": self.initialized,
            "gpu_acceleration_enabled": self.is_gpu_enabled()
        }

        if self.gpu_manager:
            gpu_status = self.gpu_manager.get_acceleration_status()
            status.update(gpu_status)

        return status

    def accelerate_portfolio_calculation(self,
                                       prices: pd.DataFrame,
                                       signals: pd.DataFrame,
                                       config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """加速投資組合計算"""
        if not self.is_gpu_enabled():
            logger.warning("GPU加速不可用，使用CPU計算")
            return self._cpu_portfolio_calculation(prices, signals, config)

        try:
            # 檢查數據大小，決定是否使用GPU
            data_size = len(prices) * len(prices.columns)
            if not self.gpu_manager.should_use_gpu(data_size):
                logger.info("數據規模較小，使用CPU計算更高效")
                return self._cpu_portfolio_calculation(prices, signals, config)

            return self._gpu_portfolio_calculation(prices, signals, config)

        except Exception as e:
            logger.error(f"GPU投資組合計算失敗: {e}")
            return self._cpu_portfolio_calculation(prices, signals, config)

    def _gpu_portfolio_calculation(self,
                                  prices: pd.DataFrame,
                                  signals: pd.DataFrame,
                                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GPU投資組合計算"""
        start_time = time.time()

        try:
            # 配置參數
            default_config = {
                "initial_cash": 100000.0,
                "fees": 0.001,
                "slippage": 0.0005,
                "call_seq": 'auto'
            }
            if config:
                default_config.update(config)

            # 將數據轉換為GPU格式
            prices_gpu = {}
            signals_gpu = {}

            for column in prices.columns:
                prices_gpu[column] = cp.asarray(prices[column].values, dtype=cp.float32)

            for column in signals.columns:
                signals_gpu[column] = cp.asarray(signals[column].values, dtype=cp.int8)

            # 執行GPU計算
            portfolio_results = {}

            for symbol in prices.columns:
                symbol_prices = prices_gpu[symbol]
                symbol_signals = signals_gpu[symbol]

                # 計算收益和持倉
                returns = self._gpu_calculate_returns(symbol_prices, symbol_signals)
                positions = self._gpu_calculate_positions(symbol_signals)

                # 計算投資組合指標
                portfolio_metrics = self._gpu_calculate_portfolio_metrics(
                    returns, positions, default_config["initial_cash"]
                )

                portfolio_results[symbol] = {
                    "returns": cp.asnumpy(returns),
                    "positions": cp.asnumpy(positions),
                    "metrics": portfolio_metrics
                }

            # 計算績效總結
            summary = self._calculate_portfolio_summary(portfolio_results)

            execution_time = time.time() - start_time

            return {
                "success": True,
                "portfolio_results": portfolio_results,
                "summary": summary,
                "execution_time": execution_time,
                "acceleration_method": "GPU"
            }

        except Exception as e:
            logger.error(f"GPU投資組合計算失敗: {e}")
            raise

    def _cpu_portfolio_calculation(self,
                                  prices: pd.DataFrame,
                                  signals: pd.DataFrame,
                                  config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """CPU投資組合計算（回退）"""
        start_time = time.time()

        try:
            # 使用VectorBT標準計算
            default_config = {
                "init_cash": 100000.0,
                "fees": 0.001,
                "slippage": 0.0005,
                "call_seq": 'auto'
            }
            if config:
                default_config.update(config)

            # 創建VectorBT投資組合
            portfolio = vbt.Portfolio.from_signals(
                prices,
                signals,
                init_cash=default_config["init_cash"],
                fees=default_config["fees"],
                slippage=default_config["slippage"],
                call_seq=default_config["call_seq"]
            )

            # 獲取結果
            returns = portfolio.returns()
            positions = portfolio.positions()
            metrics = {
                "total_return": portfolio.total_return(),
                "sharpe_ratio": portfolio.sharpe_ratio(),
                "max_drawdown": portfolio.max_drawdown(),
                "win_rate": portfolio.win_rate(),
                "trades": portfolio.trades()
            }

            execution_time = time.time() - start_time

            return {
                "success": True,
                "returns": returns,
                "positions": positions,
                "metrics": metrics,
                "execution_time": execution_time,
                "acceleration_method": "CPU"
            }

        except Exception as e:
            logger.error(f"CPU投資組合計算失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "acceleration_method": "CPU"
            }

    def _gpu_calculate_returns(self, prices: cp.ndarray, signals: cp.ndarray) -> cp.ndarray:
        """GPU計算收益"""
        try:
            # 計算價格變化
            price_changes = cp.diff(prices, prepend=prices[:1])
            price_returns = price_changes / cp.where(prices == 0, 1, prices[:-1])

            # 應用信號
            trade_returns = price_returns * signals[1:] if len(signals) > len(prices) else price_returns * signals

            return cp.concatenate([cp.array([0.0]), trade_returns])

        except Exception as e:
            logger.error(f"GPU收益計算失敗: {e}")
            raise

    def _gpu_calculate_positions(self, signals: cp.ndarray) -> cp.ndarray:
        """GPU計算持倉"""
        try:
            # 計算持倉變化
            position_changes = cp.diff(signals, prepend=signals[:1])
            cumulative_positions = cp.cumsum(position_changes)

            return cumulative_positions

        except Exception as e:
            logger.error(f"GPU持倉計算失敗: {e}")
            raise

    def _gpu_calculate_portfolio_metrics(self,
                                        returns: cp.ndarray,
                                        positions: cp.ndarray,
                                        initial_cash: float) -> Dict[str, float]:
        """GPU計算投資組合指標"""
        try:
            # 計算基本指標
            total_return = cp.sum(returns) + 1.0

            # 計算年化收益率 (假設252個交易日)
            n_periods = len(returns)
            annual_return = (total_return ** (252 / n_periods)) - 1.0 if n_periods > 0 else 0.0

            # 計算Sharpe比率 (無風險利率3%)
            excess_returns = returns - (0.03 / 252)
            sharpe_ratio = cp.mean(excess_returns) / (cp.std(excess_returns) + 1e-10) * cp.sqrt(252)

            # 計算最大回撤
            cumulative_returns = cp.cumprod(1 + returns)
            running_max = cp.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = cp.min(drawdowns)

            # 計算勝率
            winning_trades = cp.sum(returns > 0)
            total_trades = cp.sum(returns != 0)
            win_rate = winning_trades / (total_trades + 1e-10)

            return {
                "total_return": float(cp.asnumpy(total_return)),
                "annual_return": float(cp.asnumpy(annual_return)),
                "sharpe_ratio": float(cp.asnumpy(sharpe_ratio)),
                "max_drawdown": float(cp.asnumpy(max_drawdown)),
                "win_rate": float(cp.asnumpy(win_rate)),
                "total_trades": int(cp.asnumpy(total_trades))
            }

        except Exception as e:
            logger.error(f"GPU投資組合指標計算失敗: {e}")
            raise

    def _calculate_portfolio_summary(self, portfolio_results: Dict[str, Any]) -> Dict[str, Any]:
        """計算投資組合總結"""
        try:
            summary = {
                "total_symbols": len(portfolio_results),
                "successful_calculations": 0,
                "failed_calculations": 0,
                "average_metrics": {}
            }

            metrics_list = []

            for symbol, result in portfolio_results.items():
                if "metrics" in result:
                    summary["successful_calculations"] += 1
                    metrics_list.append(result["metrics"])
                else:
                    summary["failed_calculations"] += 1

            # 計算平均指標
            if metrics_list:
                metric_keys = metrics_list[0].keys()
                for key in metric_keys:
                    values = [m[key] for m in metrics_list if key in m and isinstance(m[key], (int, float))]
                    summary["average_metrics"][key] = sum(values) / len(values) if values else 0.0

            return summary

        except Exception as e:
            logger.error(f"投資組合總結計算失敗: {e}")
            return {"error": str(e)}

    def benchmark_gpu_vs_cpu(self,
                           prices: pd.DataFrame,
                           signals: pd.DataFrame,
                           iterations: int = 5) -> Dict[str, Any]:
        """GPU vs CPU性能基準測試"""
        if not self.is_gpu_enabled():
            return {"error": "GPU不可用，無法進行基準測試"}

        logger.info(f"開始GPU vs CPU基準測試 ({iterations}次迭代)...")

        results = {
            "gpu_times": [],
            "cpu_times": [],
            "speedup_ratios": [],
            "test_size": len(prices) * len(prices.columns),
            "iterations": iterations
        }

        try:
            for i in range(iterations):
                # GPU測試
                gpu_start = time.time()
                gpu_result = self._gpu_portfolio_calculation(prices, signals)
                gpu_time = time.time() - gpu_start
                results["gpu_times"].append(gpu_time)

                # CPU測試
                cpu_start = time.time()
                cpu_result = self._cpu_portfolio_calculation(prices, signals)
                cpu_time = time.time() - cpu_start
                results["cpu_times"].append(cpu_time)

                # 計算加速比
                speedup = cpu_time / gpu_time if gpu_time > 0 else 0.0
                results["speedup_ratios"].append(speedup)

                logger.info(f"迭代 {i+1}: CPU {cpu_time:.3f}s, GPU {gpu_time:.3f}s, 加速比 {speedup:.2f}x")

            # 計算統計數據
            results["avg_gpu_time"] = np.mean(results["gpu_times"])
            results["avg_cpu_time"] = np.mean(results["cpu_times"])
            results["avg_speedup"] = np.mean(results["speedup_ratios"])
            results["min_speedup"] = np.min(results["speedup_ratios"])
            results["max_speedup"] = np.max(results["speedup_ratios"])
            results["std_speedup"] = np.std(results["speedup_ratios"])

            # 生成建議
            recommendations = []
            if results["avg_speedup"] > 2.0:
                recommendations.append("GPU加速效果顯著，建議在生產環境中啟用")
            elif results["avg_speedup"] > 1.5:
                recommendations.append("GPU加速效果中等，可以考慮使用")
            else:
                recommendations.append("GPU加速效果有限，建議繼續使用CPU")

            results["recommendations"] = recommendations

            logger.info(f"基準測試完成: 平均加速比 {results['avg_speedup']:.2f}x")
            return results

        except Exception as e:
            logger.error(f"GPU vs CPU基準測試失敗: {e}")
            return {"error": str(e)}

    def cleanup(self):
        """清理資源"""
        if self.gpu_manager:
            self.gpu_manager.cleanup()
        self.initialized = False
        logger.info("VectorBT GPU集成資源已清理")

# 全局實例
_vectorbt_gpu_integration: Optional[VectorBTGPUIntegration] = None

def get_vectorbt_gpu_integration(auto_detect_gpu: bool = True) -> VectorBTGPUIntegration:
    """獲取VectorBT GPU集成實例"""
    global _vectorbt_gpu_integration
    if _vectorbt_gpu_integration is None:
        _vectorbt_gpu_integration = VectorBTGPUIntegration(auto_detect_gpu)
    return _vectorbt_gpu_integration

def initialize_vectorbt_gpu() -> bool:
    """初始化VectorBT GPU支持（便捷函數）"""
    try:
        integration = get_vectorbt_gpu_integration()
        return integration.is_gpu_enabled()
    except Exception as e:
        logger.error(f"VectorBT GPU初始化失敗: {e}")
        return False

if __name__ == "__main__":
    # 測試VectorBT GPU集成
    try:
        # 創建測試數據
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=1000, freq='D')
        symbols = ['STOCK1', 'STOCK2', 'STOCK3']

        prices = pd.DataFrame(
            np.random.uniform(50, 150, (1000, 3)),
            index=dates,
            columns=symbols
        )

        signals = pd.DataFrame(
            np.random.randint(0, 2, (1000, 3)),
            index=dates,
            columns=symbols
        )

        # 測試GPU集成
        integration = get_vectorbt_gpu_integration()

        if integration.is_gpu_enabled():
            print("✅ GPU集成已啟用")

            # 運行基準測試
            benchmark = integration.benchmark_gpu_vs_cpu(prices, signals, iterations=3)
            print(f"基準測試結果: {benchmark}")
        else:
            print("❌ GPU集成未啟用")

            # 狀態檢查
            status = integration.get_acceleration_status()
            print(f"加速狀態: {status}")

    except Exception as e:
        print(f"VectorBT GPU集成測試失敗: {e}")