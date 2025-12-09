#!/usr/bin/env python3
"""
標準化 Sharpe 比率計算模塊
Standardized Sharpe Ratio Calculation Module

統一整個系統的Sharpe比率計算方法，確保一致性和準確性
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)

class StandardizedSharpeCalculator:
    """
    標準化Sharpe比率計算器

    遵循行業標準：
    - 3%年無風險利率
    - 252交易日年化
    - 正確的年化回報率和波動率計算
    """

    # 配置常量
    RISK_FREE_RATE = 0.03  # 3%年無風險利率
    TRADING_DAYS = 252     # 年交易日數
    ANNUALIZATION_FACTOR = np.sqrt(TRADING_DAYS)

    def __init__(self, risk_free_rate: float = None, trading_days: int = None):
        """
        初始化計算器

        Args:
            risk_free_rate: 年無風險利率，默認3%
            trading_days: 年交易日數，默認252
        """
        self.risk_free_rate = risk_free_rate or self.RISK_FREE_RATE
        self.trading_days = trading_days or self.TRADING_DAYS
        self.annualization_factor = np.sqrt(self.trading_days)
        self.daily_risk_free = self.risk_free_rate / self.trading_days

    def calculate_sharpe_ratio(
        self,
        returns: Union[np.ndarray, List[float], pd.Series],
        method: str = 'standard'
    ) -> Dict[str, float]:
        """
        計算Sharpe比率

        Args:
            returns: 日收益率序列
            method: 計算方法 ('standard', 'conservative', 'robust')

        Returns:
            包含Sharpe比率和其他統計指標的字典
        """
        try:
            # 數據預處理
            returns = self._preprocess_returns(returns)

            if len(returns) < 20:
                logger.warning(f"Insufficient data points: {len(returns)} (< 20)")
                return self._empty_result()

            # 根據方法選擇計算方式
            if method == 'standard':
                sharpe = self._calculate_standard_sharpe(returns)
            elif method == 'conservative':
                sharpe = self._calculate_conservative_sharpe(returns)
            elif method == 'robust':
                sharpe = self._calculate_robust_sharpe(returns)
            else:
                raise ValueError(f"Unknown method: {method}")

            # 計算其他統計指標
            stats = self._calculate_statistics(returns)

            return {
                'sharpe_ratio': sharpe,
                'method': method,
                'risk_free_rate': self.risk_free_rate,
                'trading_days': self.trading_days,
                'data_points': len(returns),
                **stats
            }

        except Exception as e:
            logger.error(f"Sharpe calculation failed: {e}")
            return self._empty_result()

    def _preprocess_returns(self, returns: Union[np.ndarray, List[float], pd.Series]) -> np.ndarray:
        """預處理收益率數據"""
        # 轉換為numpy數組
        if not isinstance(returns, np.ndarray):
            returns = np.array(returns)

        # 移除NaN值
        returns = returns[~np.isnan(returns)]

        # 移除無窮大值
        returns = returns[np.isfinite(returns)]

        return returns

    def _calculate_standard_sharpe(self, returns: np.ndarray) -> float:
        """
        標準Sharpe比率計算方法

        公式：(年化回報率 - 無風險利率) / 年化波動率
        """
        # 計算總回報率
        total_return = np.prod(1 + returns) - 1

        # 計算年化回報率（正確的複利方法）
        years = len(returns) / self.trading_days
        if years <= 0:
            return 0.0

        annual_return = (1 + total_return) ** (1 / years) - 1

        # 計算年化波動率（使用原始收益率）
        annual_volatility = np.std(returns, ddof=1) * self.annualization_factor

        if annual_volatility == 0:
            return 0.0

        # 標準Sharpe公式
        sharpe = (annual_return - self.risk_free_rate) / annual_volatility

        return sharpe

    def _calculate_conservative_sharpe(self, returns: np.ndarray) -> float:
        """
        保守Sharpe比率計算方法

        使用算術平均回報率和更嚴格的風險調整
        """
        # 計算算術平均年化回報率
        mean_daily_return = np.mean(returns)
        annual_return = mean_daily_return * self.trading_days

        # 計算年化波動率
        annual_volatility = np.std(returns, ddof=1) * self.annualization_factor

        if annual_volatility == 0:
            return 0.0

        # 保守Sharpe計算，加入懲罰因子
        sharpe = (annual_return - self.risk_free_rate) / annual_volatility

        # 對高Sharpe值應用保守調整
        if sharpe > 2.0:
            sharpe = sharpe * 0.9  # 10%保守調整

        return sharpe

    def _calculate_robust_sharpe(self, returns: np.ndarray) -> float:
        """
        魯棒Sharpe比率計算方法

        使用中位數和其他穩健統計量
        """
        # 使用中位數計算回報（對異常值更穩健）
        median_daily_return = np.median(returns)
        annual_return = median_daily_return * self.trading_days

        # 使用絕對偏差的標準差估計（更穩健）
        mad = np.median(np.abs(returns - median_daily_return))
        robust_std = mad * 1.4826  # 轉換因子
        annual_volatility = robust_std * self.annualization_factor

        if annual_volatility == 0:
            return 0.0

        sharpe = (annual_return - self.risk_free_rate) / annual_volatility

        return sharpe

    def _calculate_statistics(self, returns: np.ndarray) -> Dict[str, float]:
        """計算其他統計指標"""
        total_return = np.prod(1 + returns) - 1
        years = len(returns) / self.trading_days

        # 年化回報率
        if years > 0:
            annual_return = (1 + total_return) ** (1 / years) - 1
        else:
            annual_return = 0.0

        # 年化波動率
        annual_volatility = np.std(returns, ddof=1) * self.annualization_factor

        # 最大回撤
        cumulative_returns = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)

        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

        # Sortino比率
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_volatility = np.std(downside_returns, ddof=1) * self.annualization_factor
            sortino_ratio = (annual_return - self.risk_free_rate) / downside_volatility
        else:
            sortino_ratio = 0.0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'daily_mean': np.mean(returns),
            'daily_std': np.std(returns, ddof=1),
            'skewness': self._calculate_skewness(returns),
            'kurtosis': self._calculate_kurtosis(returns)
        }

    def _calculate_skewness(self, returns: np.ndarray) -> float:
        """計算偏度"""
        if len(returns) < 3:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns, ddof=1)

        if std == 0:
            return 0.0

        skewness = np.mean(((returns - mean) / std) ** 3)
        return skewness

    def _calculate_kurtosis(self, returns: np.ndarray) -> float:
        """計算峰度"""
        if len(returns) < 4:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns, ddof=1)

        if std == 0:
            return 0.0

        kurtosis = np.mean(((returns - mean) / std) ** 4) - 3  # 超額峰度
        return kurtosis

    def _empty_result(self) -> Dict[str, float]:
        """返回空結果"""
        return {
            'sharpe_ratio': 0.0,
            'method': 'none',
            'risk_free_rate': self.risk_free_rate,
            'trading_days': self.trading_days,
            'data_points': 0,
            'total_return': 0.0,
            'annual_return': 0.0,
            'annual_volatility': 0.0,
            'max_drawdown': 0.0,
            'calmar_ratio': 0.0,
            'sortino_ratio': 0.0,
            'daily_mean': 0.0,
            'daily_std': 0.0,
            'skewness': 0.0,
            'kurtosis': 0.0
        }

    def validate_sharpe_calculation(self, returns: Union[np.ndarray, List[float]]) -> Dict[str, Any]:
        """
        驗證Sharpe計算的合理性

        Args:
            returns: 日收益率序列

        Returns:
            驗證結果
        """
        results = self.calculate_sharpe_ratio(returns)
        sharpe = results['sharpe_ratio']

        validation = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }

        # 檢查數據充足性
        if results['data_points'] < 50:
            validation['warnings'].append(f"Low data points: {results['data_points']} (< 50)")

        # 檢查Sharpe合理性
        if abs(sharpe) > 5:
            validation['warnings'].append(f"Extremely high Sharpe ratio: {sharpe:.3f}")
        if abs(sharpe) > 10:
            validation['errors'].append(f"Unrealistic Sharpe ratio: {sharpe:.3f}")
            validation['is_valid'] = False

        # 檢查波動率合理性
        if results['annual_volatility'] < 0.05:  # 5%以下
            validation['warnings'].append(f"Very low volatility: {results['annual_volatility']:.3f}")
        elif results['annual_volatility'] > 1.0:  # 100%以上
            validation['warnings'].append(f"Very high volatility: {results['annual_volatility']:.3f}")

        return validation

    def get_recommended_sharpe(self, returns: Union[np.ndarray, List[float]]) -> Dict[str, float]:
        """
        獲取推薦的Sharpe比率計算結果

        Args:
            returns: 日收益率序列

        Returns:
            推薦的Sharpe計算結果
        """
        # 計算多種方法的結果
        standard_result = self.calculate_sharpe_ratio(returns, 'standard')
        conservative_result = self.calculate_sharpe_ratio(returns, 'conservative')
        robust_result = self.calculate_sharpe_ratio(returns, 'robust')

        # 驗證結果
        validation = self.validate_sharpe_calculation(returns)

        # 選擇最佳結果
        if validation['is_valid']:
            # 如果驗證通過，使用標準方法
            recommended = standard_result
        else:
            # 如果有問題，使用最保守的方法
            sharpe_values = [
                standard_result['sharpe_ratio'],
                conservative_result['sharpe_ratio'],
                robust_result['sharpe_ratio']
            ]
            # 選擇絕對值最小的保守結果
            min_index = np.argmin(np.abs(sharpe_values))
            methods = ['standard', 'conservative', 'robust']
            recommended = self.calculate_sharpe_ratio(returns, methods[min_index])

        # 添加推薦信息
        recommended['validation'] = validation
        recommended['is_recommended'] = True

        return recommended


# 全局實例
_global_calculator = None

def get_sharpe_calculator(risk_free_rate: float = 0.03, trading_days: int = 252) -> StandardizedSharpeCalculator:
    """
    獲取全局Sharpe計算器實例

    Args:
        risk_free_rate: 年無風險利率
        trading_days: 年交易日數

    Returns:
        Sharpe計算器實例
    """
    global _global_calculator

    if _global_calculator is None or \
       _global_calculator.risk_free_rate != risk_free_rate or \
       _global_calculator.trading_days != trading_days:
        _global_calculator = StandardizedSharpeCalculator(risk_free_rate, trading_days)

    return _global_calculator


# 便利函數
def calculate_sharpe_ratio(
    returns: Union[np.ndarray, List[float], pd.Series],
    risk_free_rate: float = 0.03,
    method: str = 'standard'
) -> float:
    """
    便利函數：計算Sharpe比率

    Args:
        returns: 日收益率序列
        risk_free_rate: 年無風險利率，默認3%
        method: 計算方法

    Returns:
        Sharpe比率
    """
    calculator = get_sharpe_calculator(risk_free_rate)
    result = calculator.calculate_sharpe_ratio(returns, method)
    return result['sharpe_ratio']


def validate_portfolio_performance(returns: Union[np.ndarray, List[float]]) -> Dict[str, Any]:
    """
    便利函數：驗證投資組合性能

    Args:
        returns: 日收益率序列

    Returns:
        驗證結果
    """
    calculator = get_sharpe_calculator()
    return calculator.validate_sharpe_calculation(returns)


# 測試和調試
if __name__ == "__main__":
    print("🔬 標準化 Sharpe 比率計算器測試")

    # 創建測試數據
    np.random.seed(42)
    test_returns = np.random.normal(0.001, 0.02, 252)  # 一年的日回報

    calculator = StandardizedSharpeCalculator()

    # 測試不同方法
    methods = ['standard', 'conservative', 'robust']
    for method in methods:
        result = calculator.calculate_sharpe_ratio(test_returns, method)
        print(f"\n{method.upper()} 方法:")
        print(f"  Sharpe: {result['sharpe_ratio']:.4f}")
        print(f"  年化回報: {result['annual_return']:.4f} ({result['annual_return']*100:.2f}%)")
        print(f"  年化波動: {result['annual_volatility']:.4f} ({result['annual_volatility']*100:.2f}%)")

    # 驗證結果
    validation = calculator.validate_sharpe_calculation(test_returns)
    print(f"\n驗證結果:")
    print(f"  有效性: {'✅' if validation['is_valid'] else '❌'}")
    if validation['warnings']:
        print(f"  警告: {validation['warnings']}")
    if validation['errors']:
        print(f"  錯誤: {validation['errors']}")

    # 推薦結果
    recommended = calculator.get_recommended_sharpe(test_returns)
    print(f"\n推薦Sharpe比率: {recommended['sharpe_ratio']:.4f} (方法: {recommended['method']})")