#!/usr/bin/env python3
"""
安全 Sharpe 比率計算模塊
Safe Sharpe Ratio Calculation Module

解決Sharpe比率計算中的數值穩定性問題，防止異常值和除零錯誤
"""

import logging
import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SafeSharpeCalculator:
    """
    安全的Sharpe比率計算器

    實施多層保護機制：
    1. 數據有效性檢查
    2. 統計充足性驗證
    3. 邊界值限制
    4. 防禦性編程
    """

    # 配置常量
    RISK_FREE_RATE = 0.03  # 3%年無風險利率
    TRADING_DAYS = 252  # 年交易日數
    MIN_TRADES = 20  # 最少交易次數
    MIN_VOLATILITY = 0.001  # 最小波動率 (0.1%)
    MAX_VOLATILITY = 2.0  # 最大波動率 (200%)
    MAX_SHARPE = 10.0  # 最大Sharpe比率
    MIN_SHARPE = -10.0  # 最小Sharpe比率

    def __init__(self,
                 risk_free_rate: float = None,
                 trading_days: int = None,
                 min_trades: int = None,
                 enable_validation: bool = True):
        """
        初始化安全計算器

        Args:
            risk_free_rate: 年無風險利率，默認3%
            trading_days: 年交易日數，默認252
            min_trades: 最少交易次數，默認20
            enable_validation: 是否啟用嚴格驗證
        """
        self.risk_free_rate = risk_free_rate or self.RISK_FREE_RATE
        self.trading_days = trading_days or self.TRADING_DAYS
        self.min_trades = min_trades or self.MIN_TRADES
        self.enable_validation = enable_validation
        self.daily_risk_free = self.risk_free_rate / self.trading_days
        self.annualization_factor = np.sqrt(self.trading_days)

        # 統計跟蹤
        self._calculation_stats = {
            'total_calculations': 0,
            'failed_calculations': 0,
            'warnings_triggered': 0,
            'errors_prevented': 0
        }

        logger.info(f"SafeSharpeCalculator initialized: rf={self.risk_free_rate:.1%}, "
                   f"min_trades={self.min_trades}, validation={self.enable_validation}")

    def calculate_sharpe_ratio(
        self,
        returns: Union[np.ndarray, List[float], pd.Series],
        method: str = "safe_standard",
        total_trades: Optional[int] = None,
        force_calculate: bool = False
    ) -> Dict[str, Any]:
        """
        安全計算Sharpe比率

        Args:
            returns: 日收益率序列
            method: 計算方法
            total_trades: 總交易次數（用於統計驗證）
            force_calculate: 強制計算（繞過某些檢查）

        Returns:
            包含Sharpe比率和詳細診斷信息的字典
        """
        self._calculation_stats['total_calculations'] += 1

        try:
            # 第一層：數據預處理和基礎驗證
            processed_returns, preprocessing_info = self._preprocess_returns(returns)

            # 第二層：統計充足性檢查
            sufficiency_result = self._check_statistical_sufficiency(
                processed_returns, total_trades, force_calculate
            )

            if not sufficiency_result['sufficient'] and not force_calculate:
                self._calculation_stats['failed_calculations'] += 1
                return self._create_safe_result(
                    method=method,
                    failure_reason= sufficiency_result['reason'],
                    preprocessing_info=preprocessing_info
                )

            # 第三層：數值穩定性檢查
            stability_result = self._check_numerical_stability(processed_returns)

            if not stability_result['stable'] and not force_calculate:
                self._calculation_stats['errors_prevented'] += 1
                return self._create_safe_result(
                    method=method,
                    failure_reason=stability_result['reason'],
                    preprocessing_info=preprocessing_info
                )

            # 第四層：執行安全計算
            calculation_result = self._safe_sharpe_calculation(
                processed_returns, method, preprocessing_info
            )

            # 第五層：結果合理性驗證
            if self.enable_validation and not force_calculate:
                validation_result = self._validate_calculation_result(calculation_result)
                if not validation_result['valid']:
                    self._calculation_stats['errors_prevented'] += 1
                    return self._create_safe_result(
                        method=method,
                        failure_reason=validation_result['reason'],
                        preprocessing_info=preprocessing_info
                    )
                    calculation_result['sharpe_ratio'] = validation_result['corrected_value']
                    self._calculation_stats['warnings_triggered'] += 1

            return calculation_result

        except Exception as e:
            logger.error(f"Safe Sharpe calculation failed: {e}")
            self._calculation_stats['failed_calculations'] += 1
            return self._create_safe_result(
                method=method,
                failure_reason=f"Calculation exception: {str(e)}",
                exception=True
            )

    def _preprocess_returns(self, returns: Union[np.ndarray, List[float], pd.Series]) -> Tuple[np.ndarray, Dict[str, Any]]:
        """預處理收益率數據"""
        preprocessing_info = {
            'original_length': 0,
            'nan_count': 0,
            'inf_count': 0,
            'final_length': 0
        }

        # 轉換為numpy數組
        if not isinstance(returns, np.ndarray):
            returns = np.array(returns)

        preprocessing_info['original_length'] = len(returns)

        # 移除NaN值
        nan_mask = np.isnan(returns)
        preprocessing_info['nan_count'] = np.sum(nan_mask)
        returns = returns[~nan_mask]

        # 移除無窮大值
        inf_mask = np.isinf(returns)
        preprocessing_info['inf_count'] = np.sum(inf_mask)
        returns = returns[~inf_mask]

        preprocessing_info['final_length'] = len(returns)

        # 檢查是否有足夠的數據
        if len(returns) < 10:
            raise ValueError(f"Insufficient valid returns: {len(returns)} (< 10)")

        return returns, preprocessing_info

    def _check_statistical_sufficiency(self,
                                     returns: np.ndarray,
                                     total_trades: Optional[int],
                                     force_calculate: bool) -> Dict[str, Any]:
        """檢查統計充足性"""
        result = {
            'sufficient': True,
            'reason': None,
            'warnings': []
        }

        # 檢查數據點數量
        if len(returns) < self.min_trades:
            result['sufficient'] = False
            result['reason'] = f"Insufficient data points: {len(returns)} (< {self.min_trades})"
            return result

        # 檢查交易次數
        if total_trades is not None and total_trades < self.min_trades:
            result['sufficient'] = False
            result['reason'] = f"Insufficient trades: {total_trades} (< {self.min_trades})"
            return result

        # 檢查時間跨度
        if len(returns) < self.trading_days // 4:  # 少於3個月數據
            result['warnings'].append(f"Limited time span: {len(returns)} days (< 3 months)")

        # 檢查勝率合理性
        positive_returns = np.sum(returns > 0)
        win_rate = positive_returns / len(returns)
        if win_rate > 0.8 or win_rate < 0.2:
            result['warnings'].append(f"Unusual win rate: {win_rate:.2%}")

        return result

    def _check_numerical_stability(self, returns: np.ndarray) -> Dict[str, Any]:
        """檢查數值穩定性"""
        result = {
            'stable': True,
            'reason': None,
            'warnings': []
        }

        # 檢查波動率
        volatility = np.std(returns, ddof=1)
        if volatility < self.MIN_VOLATILITY:
            result['stable'] = False
            result['reason'] = f"Volatility too low: {volatility:.6f} (< {self.MIN_VOLATILITY})"
            return result

        if volatility > self.MAX_VOLATILITY:
            result['stable'] = False
            result['reason'] = f"Volatility too high: {volatility:.4f} (> {self.MAX_VOLATILITY})"
            return result

        # 檢查極端收益率
        extreme_threshold = 5 * volatility
        extreme_returns = np.abs(returns) > extreme_threshold
        extreme_count = np.sum(extreme_returns)

        if extreme_count > 0:
            result['warnings'].append(f"Found {extreme_count} extreme returns (>{extreme_threshold:.2%})")

        # 檢查數據連續性（大量重複值）
        unique_values = len(np.unique(returns))
        if unique_values < len(returns) * 0.1:
            result['warnings'].append(f"Low data diversity: {unique_values}/{len(returns)} unique values")

        return result

    def _safe_sharpe_calculation(self,
                               returns: np.ndarray,
                               method: str,
                               preprocessing_info: Dict[str, Any]) -> Dict[str, Any]:
        """執行安全的Sharpe計算"""

        if method == "safe_standard":
            sharpe, stats = self._calculate_safe_standard_sharpe(returns)
        elif method == "robust_median":
            sharpe, stats = self._calculate_robust_median_sharpe(returns)
        elif method == "conservative":
            sharpe, stats = self._calculate_conservative_sharpe(returns)
        else:
            raise ValueError(f"Unknown calculation method: {method}")

        # 應用邊界限制
        sharpe = np.clip(sharpe, self.MIN_SHARPE, self.MAX_SHARPE)

        result = {
            'sharpe_ratio': sharpe,
            'method': method,
            'risk_free_rate': self.risk_free_rate,
            'trading_days': self.trading_days,
            'data_points': len(returns),
            'preprocessing_info': preprocessing_info,
            **stats
        }

        return result

    def _calculate_safe_standard_sharpe(self, returns: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """安全的標準Sharpe計算"""

        # 計算總回報和年化回報（幾何複合）
        total_return = np.prod(1 + returns) - 1
        years = len(returns) / self.trading_days

        if years <= 0:
            return 0.0, {'annual_return': 0.0, 'annual_volatility': 0.0}

        annual_return = (1 + total_return) ** (1 / years) - 1

        # 計算年化波動率
        volatility = np.std(returns, ddof=1)
        annual_volatility = volatility * self.annualization_factor

        # 安全檢查：防止除零
        if annual_volatility < self.MIN_VOLATILITY:
            annual_volatility = self.MIN_VOLATILITY
            logger.warning(f"Applied minimum volatility threshold: {self.MIN_VOLATILITY}")

        # 計算日化超額收益
        excess_returns = returns - self.daily_risk_free

        # 安全Sharpe計算
        if len(excess_returns) > 1 and np.std(excess_returns, ddof=1) > 0:
            sharpe = np.mean(excess_returns) / np.std(excess_returns, ddof=1) * self.annualization_factor
        else:
            sharpe = 0.0
            logger.warning("Insufficient variation in excess returns, using Sharpe = 0")

        return sharpe, {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'daily_mean': np.mean(returns),
            'daily_std': volatility
        }

    def _calculate_robust_median_sharpe(self, returns: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """穩健的中位數Sharpe計算"""

        # 使用中位數計算回報
        median_daily_return = np.median(returns)
        annual_return = median_daily_return * self.trading_days

        # 使用絕對偏差估計波動率
        mad = np.median(np.abs(returns - median_daily_return))
        robust_std = mad * 1.4826  # 標準差轉換因子
        annual_volatility = robust_std * self.annualization_factor

        # 應用最小波動率限制
        if annual_volatility < self.MIN_VOLATILITY:
            annual_volatility = self.MIN_VOLATILITY

        # 計算穩健Sharpe
        if robust_std > 0:
            sharpe = (median_daily_return - self.daily_risk_free) / robust_std * self.annualization_factor
        else:
            sharpe = 0.0

        return sharpe, {
            'total_return': np.prod(1 + returns) - 1,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'daily_median': median_daily_return,
            'robust_std': robust_std
        }

    def _calculate_conservative_sharpe(self, returns: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """保守的Sharpe計算"""

        # 使用算術平均（保守方法）
        mean_daily_return = np.mean(returns)
        annual_return = mean_daily_return * self.trading_days

        # 使用較大的波動率估計
        volatility = np.std(returns, ddof=1)
        annual_volatility = volatility * self.annualization_factor

        # 應用保守調整
        if annual_volatility < self.MIN_VOLATILITY:
            annual_volatility = self.MIN_VOLATILITY

        # 應用波動率的保守調整（增加10%）
        annual_volatility *= 1.1

        # 計算保守Sharpe
        if annual_volatility > 0:
            sharpe = (annual_return - self.risk_free_rate) / annual_volatility

            # 對高Sharpe應用額外保守調整
            if sharpe > 2.0:
                sharpe = 2.0 + (sharpe - 2.0) * 0.5  # 超過2的部分減半
            elif sharpe < -2.0:
                sharpe = -2.0 + (sharpe + 2.0) * 0.5  # 超過-2的部分減半
        else:
            sharpe = 0.0

        return sharpe, {
            'total_return': np.prod(1 + returns) - 1,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'daily_mean': mean_daily_return,
            'daily_std': volatility,
            'conservative_adjustment': 1.1
        }

    def _validate_calculation_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """驗證計算結果的合理性"""
        sharpe = result['sharpe_ratio']

        validation = {
            'valid': True,
            'reason': None,
            'corrected_value': None
        }

        # 檢查是否包含NaN或無窮大
        if not np.isfinite(sharpe):
            validation['valid'] = False
            validation['reason'] = f"Non-finite Sharpe result: {sharpe}"
            validation['corrected_value'] = 0.0
            return validation

        # 檢查是否超過合理的Sharpe範圍
        if abs(sharpe) > 5.0:
            validation['warnings'] = f"Extremely high Sharpe ratio: {sharpe:.3f}"

        if abs(sharpe) > 7.0:
            validation['valid'] = False
            validation['reason'] = f"Unrealistic Sharpe ratio: {sharpe:.3f}"
            # 應用合理的限制
            validation['corrected_value'] = np.sign(sharpe) * min(abs(sharpe), self.MAX_SHARPE)

        return validation

    def _create_safe_result(self,
                          method: str,
                          failure_reason: str,
                          preprocessing_info: Optional[Dict[str, Any]] = None,
                          exception: bool = False) -> Dict[str, Any]:
        """創建安全的默認結果"""

        if exception:
            logger.error(f"Sharpe calculation exception: {failure_reason}")
        else:
            logger.warning(f"Sharpe calculation prevented: {failure_reason}")

        return {
            'sharpe_ratio': 0.0,
            'method': method,
            'risk_free_rate': self.risk_free_rate,
            'trading_days': self.trading_days,
            'data_points': 0,
            'failure_reason': failure_reason,
            'preprocessing_info': preprocessing_info or {},
            'total_return': 0.0,
            'annual_return': 0.0,
            'annual_volatility': 0.0,
            'daily_mean': 0.0,
            'daily_std': 0.0,
            'is_safe_fallback': True
        }

    def get_calculation_stats(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        stats = self._calculation_stats.copy()
        if stats['total_calculations'] > 0:
            stats['success_rate'] = 1 - (stats['failed_calculations'] / stats['total_calculations'])
            stats['warning_rate'] = stats['warnings_triggered'] / stats['total_calculations']
            stats['error_prevention_rate'] = stats['errors_prevented'] / stats['total_calculations']
        else:
            stats['success_rate'] = 0.0
            stats['warning_rate'] = 0.0
            stats['error_prevention_rate'] = 0.0

        return stats

    def diagnose_portfolio_returns(self, returns: Union[np.ndarray, List[float]]) -> Dict[str, Any]:
        """診斷投資組合收益率數據的質量"""

        try:
            processed_returns, preprocessing_info = self._preprocess_returns(returns)

            diagnosis = {
                'data_quality': 'good',
                'issues': [],
                'recommendations': [],
                'statistics': {}
            }

            # 基本統計
            diagnosis['statistics'] = {
                'length': len(processed_returns),
                'mean': float(np.mean(processed_returns)),
                'std': float(np.std(processed_returns, ddof=1)),
                'min': float(np.min(processed_returns)),
                'max': float(np.max(processed_returns)),
                'skewness': float(self._calculate_skewness(processed_returns)),
                'kurtosis': float(self._calculate_kurtosis(processed_returns))
            }

            # 數據質量檢查
            if preprocessing_info['nan_count'] > 0:
                diagnosis['issues'].append(f"Found {preprocessing_info['nan_count']} NaN values")

            if preprocessing_info['inf_count'] > 0:
                diagnosis['issues'].append(f"Found {preprocessing_info['inf_count']} infinite values")
                diagnosis['data_quality'] = 'poor'

            # 波動率檢查
            volatility = diagnosis['statistics']['std']
            if volatility < self.MIN_VOLATILITY:
                diagnosis['issues'].append(f"Very low volatility: {volatility:.6f}")
                diagnosis['data_quality'] = 'questionable'

            # 交易次數估計（基非零收益）
            non_zero_returns = np.sum(np.abs(processed_returns) > 1e-10)
            if non_zero_returns < self.min_trades:
                diagnosis['issues'].append(f"Estimated few trades: {non_zero_returns}")
                diagnosis['recommendations'].append("Consider longer backtest period")
                diagnosis['data_quality'] = 'questionable'

            return diagnosis

        except Exception as e:
            return {
                'data_quality': 'error',
                'issues': [f"Diagnosis failed: {str(e)}"],
                'recommendations': [],
                'statistics': {}
            }

    def _calculate_skewness(self, returns: np.ndarray) -> float:
        """計算偏度"""
        if len(returns) < 3:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns, ddof=1)

        if std == 0:
            return 0.0

        return float(np.mean(((returns - mean) / std) ** 3))

    def _calculate_kurtosis(self, returns: np.ndarray) -> float:
        """計算峰度"""
        if len(returns) < 4:
            return 0.0

        mean = np.mean(returns)
        std = np.std(returns, ddof=1)

        if std == 0:
            return 0.0

        return float(np.mean(((returns - mean) / std) ** 4) - 3)


# 全局安全計算器實例
_global_safe_calculator = None


def get_safe_sharpe_calculator(
    risk_free_rate: float = 0.03,
    trading_days: int = 252,
    enable_validation: bool = True
) -> SafeSharpeCalculator:
    """獲取全局安全Sharpe計算器實例"""
    global _global_safe_calculator

    if (_global_safe_calculator is None or
        _global_safe_calculator.risk_free_rate != risk_free_rate or
        _global_safe_calculator.trading_days != trading_days):

        _global_safe_calculator = SafeSharpeCalculator(
            risk_free_rate=risk_free_rate,
            trading_days=trading_days,
            enable_validation=enable_validation
        )

    return _global_safe_calculator


def safe_calculate_sharpe_ratio(
    returns: Union[np.ndarray, List[float], pd.Series],
    risk_free_rate: float = 0.03,
    method: str = "safe_standard",
    total_trades: Optional[int] = None,
    enable_validation: bool = True
) -> float:
    """
    便利函數：安全計算Sharpe比率

    Args:
        returns: 日收益率序列
        risk_free_rate: 年無風險利率
        method: 計算方法
        total_trades: 總交易次數
        enable_validation: 是否啟用驗證

    Returns:
        安全的Sharpe比率
    """
    calculator = get_safe_sharpe_calculator(risk_free_rate, enable_validation=enable_validation)
    result = calculator.calculate_sharpe_ratio(returns, method, total_trades)
    return result['sharpe_ratio']


def validate_portfolio_returns(returns: Union[np.ndarray, List[float]]) -> Dict[str, Any]:
    """
    便利函數：驗證投資組合收益率數據質量

    Args:
        returns: 日收益率序列

    Returns:
        診斷結果
    """
    calculator = get_safe_sharpe_calculator()
    return calculator.diagnose_portfolio_returns(returns)


# 測試和調試
if __name__ == "__main__":
    print("🛡️ 安全 Sharpe 比率計算器測試")

    # 創建安全計算器
    calculator = SafeSharpeCalculator(enable_validation=True)

    # 測試1：正常數據
    print("\n測試1：正常市場數據")
    np.random.seed(42)
    normal_returns = np.random.normal(0.001, 0.02, 252)  # 正常的日收益率

    result = calculator.calculate_sharpe_ratio(normal_returns, method="safe_standard", total_trades=50)
    print(f"  Sharpe: {result['sharpe_ratio']:.4f}")
    print(f"  年化回報: {result['annual_return']:.4f} ({result['annual_return']*100:.2f}%)")
    print(f"  年化波動: {result['annual_volatility']:.4f} ({result['annual_volatility']*100:.2f}%)")

    # 測試2：低波動率數據（除零風險）
    print("\n測試2：低波動率數據")
    low_vol_returns = np.random.normal(0.0001, 0.0001, 100)  # 極低波動

    result = calculator.calculate_sharpe_ratio(low_vol_returns, method="safe_standard")
    print(f"  Sharpe: {result['sharpe_ratio']:.4f}")
    if 'failure_reason' in result:
        print(f"  失敗原因: {result['failure_reason']}")

    # 測試3：單次交易數據
    print("\n測試3：單次交易數據")
    single_trade_returns = np.zeros(252)
    single_trade_returns[100] = 0.05  # 單次5%收益

    result = calculator.calculate_sharpe_ratio(single_trade_returns, total_trades=1)
    print(f"  Sharpe: {result['sharpe_ratio']:.4f}")
    if 'failure_reason' in result:
        print(f"  失敗原因: {result['failure_reason']}")

    # 測試4：極端值數據
    print("\n測試4：包含極端值的數據")
    extreme_returns = normal_returns.copy()
    extreme_returns[50] = 0.5  # 50%單日收益

    result = calculator.calculate_sharpe_ratio(extreme_returns, method="safe_standard")
    print(f"  Sharpe: {result['sharpe_ratio']:.4f}")

    # 診斷功能測試
    print("\n診斷功能測試：")
    diagnosis = calculator.diagnose_portfolio_returns(extreme_returns)
    print(f"  數據質量: {diagnosis['data_quality']}")
    print(f"  問題: {diagnosis['issues']}")
    print(f"  統計: 長度={diagnosis['statistics']['length']}, "
          f"均值={diagnosis['statistics']['mean']:.6f}, "
          f"波動={diagnosis['statistics']['std']:.6f}")

    # 計算統計
    print("\n計算器統計：")
    stats = calculator.get_calculation_stats()
    print(f"  總計算次數: {stats['total_calculations']}")
    print(f"  失敗次數: {stats['failed_calculations']}")
    print(f"  成功率: {stats['success_rate']:.2%}")
    print(f"  錯誤預防率: {stats['error_prevention_rate']:.2%}")

    print("\n✅ 安全Sharpe計算器測試完成")