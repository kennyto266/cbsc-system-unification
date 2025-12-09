#!/usr/bin/env python3
"""
專業級夏普比率計算器
基於行業標準，不依賴外部金融庫
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union

class ProfessionalSharpeCalculator:
    """
    專業級夏普比率計算器
    遵循行業標準和最佳實踐
    """

    def __init__(self, risk_free_rate: float = 0.03, trading_days: int = 252):
        """
        初始化計算器

        Args:
            risk_free_rate: 年無風險利率 (默認3%)
            trading_days: 年交易日數 (默認252)
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days = trading_days
        self.daily_rf = (1 + risk_free_rate) ** (1/trading_days) - 1

    def calculate_sharpe_ratio(self, returns: Union[np.ndarray, List[float], pd.Series]) -> Dict[str, float]:
        """
        使用多種方法計算夏普比率

        Args:
            returns: 日回報率數組

        Returns:
            Dict: 包含多種夏普比率計算方法的字典
        """
        # 轉換為numpy數組
        if not isinstance(returns, np.ndarray):
            returns = np.array(returns)

        # 移除NaN值
        returns = returns[~np.isnan(returns)]

        if len(returns) < 2:
            return self._empty_result()

        # 計算超額回報
        excess_returns = returns - self.daily_rf

        # 方法1: 標準方法 (推薦)
        sharpe_standard = self._calculate_standard_sharpe(returns, excess_returns)

        # 方法2: 年化回報率方法
        sharpe_annual_return = self._calculate_annual_return_sharpe(returns, excess_returns)

        # 方法3: 保守方法 (使用樣本統計)
        sharpe_conservative = self._calculate_conservative_sharpe(returns, excess_returns)

        # 方法4: QuantStats方法 (如果可用)
        sharpe_quantstats = self._calculate_quantstats_sharpe(returns)

        return {
            'standard': sharpe_standard,
            'annual_return': sharpe_annual_return,
            'conservative': sharpe_conservative,
            'quantstats': sharpe_quantstats,
            'daily_rf': self.daily_rf,
            'excess_return_mean': np.mean(excess_returns),
            'excess_return_std': np.std(excess_returns, ddof=1),
            'data_points': len(returns),
            'volatility_annual': np.std(excess_returns, ddof=1) * np.sqrt(self.trading_days)
        }

    def _calculate_standard_sharpe(self, returns: np.ndarray, excess_returns: np.ndarray) -> float:
        """
        標準夏普比率計算方法 - 使用正確公式
        """
        # 計算年化回報率
        annual_return = (1 + np.mean(returns))**self.trading_days - 1

        # 計算年化無風險利率
        annual_rf = self.risk_free_rate

        # 計算年化波動率 (使用原始回報的標準差 - 關鍵修正!)
        annual_volatility = np.std(returns, ddof=1) * np.sqrt(self.trading_days)

        if annual_volatility == 0:
            return 0.0

        # 正確的夏普比率公式: (年化回報 - 無風險利率) / 年化波動率
        sharpe = (annual_return - annual_rf) / annual_volatility
        return sharpe

    def _calculate_annual_return_sharpe(self, returns: np.ndarray, excess_returns: np.ndarray) -> float:
        """
        基於年化回報率的夏普比率計算 (修正版)
        """
        # 計算年化回報率
        total_return = np.prod(1 + returns) - 1
        years = len(returns) / self.trading_days
        annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0

        # 計算年化波動率 (使用原始回報 - 關鍵修正!)
        annual_volatility = np.std(returns, ddof=1) * np.sqrt(self.trading_days)

        if annual_volatility == 0:
            return 0.0

        sharpe = (annual_return - self.risk_free_rate) / annual_volatility
        return sharpe

    def _calculate_conservative_sharpe(self, returns: np.ndarray, excess_returns: np.ndarray) -> float:
        """
        保守的夏普比率計算 (使用更嚴格的統計 - 修正版)
        """
        # 計算年化回報率 (使用幾何平均 - 更保守)
        total_return = np.prod(1 + returns) - 1
        years = len(returns) / self.trading_days
        annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0

        # 計算年化波動率 (使用原始回報 - 關鍵修正!)
        annual_volatility = np.std(returns, ddof=1) * np.sqrt(self.trading_days)

        if annual_volatility == 0:
            return 0.0

        # 保守的夏普比率公式，加上5%保守調整
        conservative_sharpe = (annual_return - self.risk_free_rate) / annual_volatility
        return conservative_sharpe * 0.95  # 5%保守調整

    def _calculate_quantstats_sharpe(self, returns: np.ndarray) -> float:
        """
        使用QuantStats計算夏普比率 (如果可用)
        """
        try:
            import quantstats as qs
            # QuantStats使用年化無風險利率
            returns_series = pd.Series(returns)
            sharpe = qs.stats.sharpe(returns_series, rf=self.risk_free_rate)
            return sharpe if not np.isnan(sharpe) else 0.0
        except ImportError:
            return None
        except Exception:
            return None

    def _empty_result(self) -> Dict[str, float]:
        """
        返回空結果字典
        """
        return {
            'standard': 0.0,
            'annual_return': 0.0,
            'conservative': 0.0,
            'quantstats': None,
            'daily_rf': self.daily_rf,
            'excess_return_mean': 0.0,
            'excess_return_std': 0.0,
            'data_points': 0,
            'volatility_annual': 0.0
        }

    def validate_calculation(self, returns: Union[np.ndarray, List[float]]) -> Dict[str, Any]:
        """
        驗證計算的一致性和正確性

        Args:
            returns: 日回報率數組

        Returns:
            Dict: 驗證結果
        """
        results = self.calculate_sharpe_ratio(returns)

        # 提取主要方法結果
        sharpe_values = [
            results['standard'],
            results['annual_return'],
            results['conservative']
        ]

        # 移除None值
        sharpe_values = [s for s in sharpe_values if s is not None]

        if len(sharpe_values) < 2:
            return {
                'consistent': False,
                'error': 'Insufficient calculation methods',
                'results': results
            }

        # 計算方法間差異
        max_sharpe = max(sharpe_values)
        min_sharpe = min(sharpe_values)
        diff = max_sharpe - min_sharpe
        diff_pct = (diff / max_sharpe) * 100 if max_sharpe != 0 else 0

        # 一致性評估
        if diff_pct < 1:
            consistency_level = "EXCELLENT"
        elif diff_pct < 5:
            consistency_level = "GOOD"
        elif diff_pct < 10:
            consistency_level = "ACCEPTABLE"
        else:
            consistency_level = "POOR"

        return {
            'consistent': diff_pct < 10,
            'consistency_level': consistency_level,
            'max_difference_pct': diff_pct,
            'standard_sharpe': results['standard'],
            'all_results': results,
            'recommendation': results['standard'] if diff_pct < 10 else "Review calculation methods"
        }

    def get_recommended_sharpe(self, returns: Union[np.ndarray, List[float]]) -> float:
        """
        獲取推薦的夏普比率

        Args:
            returns: 日回報率數組

        Returns:
            float: 推薦的夏普比率
        """
        validation = self.validate_calculation(returns)

        if validation['consistent']:
            return validation['standard_sharpe']
        else:
            # 如果不一致，使用最保守的方法
            results = self.calculate_sharpe_ratio(returns)
            return min([s for s in [results['standard'], results['annual_return'], results['conservative']] if s is not None])

# 測試和驗證
def main():
    """主程序 - 測試專業級夏普比率計算器"""
    print("🔬 專業級夏普比率計算器測試")

    calculator = ProfessionalSharpeCalculator()

    # 創建測試數據
    np.random.seed(42)
    test_returns = np.random.normal(0.001, 0.02, 252)  # 一年的日回報

    print(f"\n📊 測試數據: {len(test_returns)} 個交易日")
    print(f"日回報均值: {np.mean(test_returns):.6f}")
    print(f"日回報標準差: {np.std(test_returns, ddof=1):.6f}")

    # 計算夏普比率
    results = calculator.calculate_sharpe_ratio(test_returns)

    print(f"\n🔢 多方法夏普比率計算:")
    print(f"標準方法: {results['standard']:.4f}")
    print(f"年化回報方法: {results['annual_return']:.4f}")
    print(f"保守方法: {results['conservative']:.4f}")
    print(f"QuantStats: {results['quantstats'] if results['quantstats'] else 'N/A'}")

    # 驗證計算一致性
    validation = calculator.validate_calculation(test_returns)
    print(f"\n✅ 計算驗證:")
    print(f"一致性: {validation['consistent']}")
    print(f"一致性級別: {validation['consistency_level']}")
    print(f"最大差異: {validation['max_difference_pct']:.2f}%")
    print(f"推薦夏普: {validation['standard_sharpe']:.4f}")

    # 獲取推薦值
    recommended = calculator.get_recommended_sharpe(test_returns)
    print(f"🎯 最終推薦夏普比率: {recommended:.4f}")

    print(f"\n📈 詳細統計:")
    print(f"日無風險利率: {results['daily_rf']:.6f}")
    print(f"超額回報均值: {results['excess_return_mean']:.6f}")
    print(f"超額回報標準差: {results['excess_return_std']:.6f}")
    print(f"年化波動率: {results['volatility_annual']:.4f}")

if __name__ == "__main__":
    main()