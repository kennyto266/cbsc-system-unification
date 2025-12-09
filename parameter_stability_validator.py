#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
參數穩定性驗證系統
Parameter Stability Validation System

為0-300全參數優化結果提供專業級的時間穩定性驗證、敏感性分析和樣本外測試
Provides professional-grade time stability validation, sensitivity analysis, and out-of-sample testing for 0-300 parameter optimization results
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.model_selection import TimeSeriesSplit
import warnings
warnings.filterwarnings('ignore')

# 導入核心模塊
from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine, BacktestResult
from simplified_system.src.api.stock_api import get_hk_stock_data
from multi_objective_performance_evaluator import MultiObjectivePerformanceEvaluator, PerformanceMetrics

logger = logging.getLogger(__name__)

@dataclass
class StabilityTestConfig:
    """穩定性測試配置"""
    # 時間窗口設置
    min_test_period: int = 90  # 最小測試期（天）
    validation_windows: List[int] = field(default_factory=lambda: [30, 60, 90, 180])
    rolling_window_size: int = 252  # 滾動窗口大小（1年）

    # 穩定性閾值
    sharpe_stability_threshold: float = 0.3  # Sharpe標準差閾值
    performance_correlation_threshold: float = 0.7  # 性能相關性閾值
    max_parameter_drift: float = 0.2  # 最大參數漂移

    # 敏感性分析
    sensitivity_step_sizes: Dict[str, float] = field(default_factory=lambda: {
        'rsi_period': 5.0,
        'rsi_oversold': 2.0,
        'rsi_overbought': 2.0,
        'macd_fast': 2.0,
        'macd_slow': 5.0,
        'macd_signal': 1.0
    })

    # 樣本外測試
    out_of_sample_ratio: float = 0.3  # 樣本外比例
    walk_forward_windows: int = 5  # 前向分析窗口數

@dataclass
class StabilityResult:
    """穩定性測試結果"""
    parameter_set: Dict[str, Any]
    overall_stability_score: float
    time_stability_metrics: Dict[str, float]
    sensitivity_metrics: Dict[str, Any]
    out_of_sample_performance: Dict[str, float]
    walk_forward_results: Dict[str, Any]
    recommendations: List[str]

class ParameterStabilityValidator:
    """
    參數穩定性驗證系統

    提供專業級的參數驗證功能：
    - 多時間窗口穩定性測試
    - 參數敏感性分析
    - 樣本外性能驗證
    - 前向分析（Walk Forward）
    - 參數漂移檢測
    - 市場適應性分析
    """

    def __init__(self, config: Optional[StabilityTestConfig] = None):
        """
        初始化參數穩定性驗證器

        Args:
            config: 穩定性測試配置
        """
        self.config = config or StabilityTestConfig()

        # 初始化核心組件
        self.vectorbt_engine = VectorBTEngine()
        self.performance_evaluator = MultiObjectivePerformanceEvaluator()

        # 驗證統計
        self.validation_stats = {
            'parameters_validated': 0,
            'stability_tests_completed': 0,
            'sensitivity_analyses_completed': 0,
            'out_of_sample_tests_completed': 0
        }

        logger.info("Parameter Stability Validator initialized")

    def validate_parameter_stability(
        self,
        optimal_parameters: List[Dict[str, Any]],
        strategy_type: str,
        symbol: str = "0700.HK",
        data_period: int = 730  # 2年數據用於穩定性測試
    ) -> Dict[str, Any]:
        """
        驗證參數穩定性

        Args:
            optimal_parameters: 最優參數列表
            strategy_type: 策略類型
            symbol: 股票代碼
            data_period: 數據期間

        Returns:
            穩定性驗證結果
        """
        logger.info(f"Starting stability validation for {len(optimal_parameters)} parameter sets")

        # 獲取長期數據
        logger.info(f"Loading {data_period} days of historical data for {symbol}")
        full_data = get_hk_stock_data(symbol, data_period)

        if len(full_data) < self.config.min_test_period * 2:
            raise ValueError(f"Insufficient data for stability testing. Need at least {self.config.min_test_period * 2} days")

        validation_results = []

        for i, params in enumerate(optimal_parameters[:10]):  # 限制驗證前10個最優參數
            try:
                logger.info(f"Validating parameter set {i+1}/{len(optimal_parameters)}")

                # 時間穩定性測試
                time_stability = self._test_time_stability(params, strategy_type, full_data)

                # 敏感性分析
                sensitivity_analysis = self._perform_sensitivity_analysis(params, strategy_type, full_data)

                # 樣本外測試
                out_of_sample_test = self._perform_out_of_sample_test(params, strategy_type, full_data)

                # 前向分析
                walk_forward_test = self._perform_walk_forward_analysis(params, strategy_type, full_data)

                # 計算總體穩定性評分
                stability_score = self._calculate_overall_stability_score(
                    time_stability, sensitivity_analysis, out_of_sample_test, walk_forward_test
                )

                # 生成建議
                recommendations = self._generate_stability_recommendations(
                    time_stability, sensitivity_analysis, out_of_sample_test, walk_forward_test
                )

                stability_result = StabilityResult(
                    parameter_set=params,
                    overall_stability_score=stability_score,
                    time_stability_metrics=time_stability,
                    sensitivity_metrics=sensitivity_analysis,
                    out_of_sample_performance=out_of_sample_test,
                    walk_forward_results=walk_forward_test,
                    recommendations=recommendations
                )

                validation_results.append(stability_result)

            except Exception as e:
                logger.warning(f"Failed to validate parameters {params}: {e}")
                continue

        # 更新統計
        self.validation_stats['parameters_validated'] += len(validation_results)

        # 分析整體結果
        overall_analysis = self._analyze_overall_stability(validation_results)

        return {
            'validation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'strategy_type': strategy_type,
            'data_period': data_period,
            'individual_results': validation_results,
            'overall_analysis': overall_analysis,
            'stable_parameters': [r for r in validation_results if r.overall_stability_score >= 70]
        }

    def _test_time_stability(
        self,
        params: Dict[str, Any],
        strategy_type: str,
        data: pd.DataFrame
    ) -> Dict[str, float]:
        """時間穩定性測試"""
        logger.info("Performing time stability analysis...")

        stability_metrics = {}

        # 不同時間窗口的性能測試
        window_performances = []

        for window_size in self.config.validation_windows:
            if len(data) < window_size * 2:
                continue

            # 滾動窗口測試
            rolling_performances = []

            for start_idx in range(0, len(data) - window_size, window_size // 2):
                end_idx = start_idx + window_size
                window_data = data.iloc[start_idx:end_idx]

                if len(window_data) < self.config.min_test_period:
                    continue

                try:
                    # 轉換參數格式
                    strategy_params = self._convert_parameters(params, strategy_type)

                    # 執行回測
                    result = self.vectorbt_engine.backtest_strategy(
                        data=window_data,
                        strategy=self._get_strategy_name(strategy_type),
                        parameters=strategy_params,
                        symbol="0700.HK"
                    )

                    rolling_performances.append({
                        'sharpe_ratio': result.sharpe_ratio,
                        'max_drawdown': result.max_drawdown,
                        'win_rate': result.win_rate,
                        'total_return': result.total_return
                    })

                except Exception as e:
                    logger.warning(f"Window test failed: {e}")
                    continue

            if rolling_performances:
                window_performances.extend(rolling_performances)

        # 計算穩定性指標
        if window_performances:
            sharpe_values = [p['sharpe_ratio'] for p in window_performances]
            return_values = [p['total_return'] for p in window_performances]
            drawdown_values = [p['max_drawdown'] for p in window_performances]
            win_rate_values = [p['win_rate'] for p in window_performances]

            stability_metrics.update({
                'sharpe_mean': np.mean(sharpe_values),
                'sharpe_std': np.std(sharpe_values),
                'sharpe_stability': 1 - (np.std(sharpe_values) / abs(np.mean(sharpe_values)) if np.mean(sharpe_values) != 0 else 0),
                'return_consistency': 1 - (np.std(return_values) / abs(np.mean(return_values)) if np.mean(return_values) != 0 else 0),
                'drawdown_consistency': 1 - (np.std(drawdown_values) / abs(np.mean(drawdown_values)) if np.mean(drawdown_values) != 0 else 0),
                'win_rate_stability': 1 - (np.std(win_rate_values) / np.mean(win_rate_values) if np.mean(win_rate_values) > 0 else 0),
                'positive_periods_ratio': len([r for r in return_values if r > 0]) / len(return_values)
            })

        # 長期趨勢穩定性
        if len(data) >= self.config.rolling_window_size:
            trend_stability = self._test_trend_stability(params, strategy_type, data)
            stability_metrics.update(trend_stability)

        return stability_metrics

    def _test_trend_stability(
        self,
        params: Dict[str, Any],
        strategy_type: str,
        data: pd.DataFrame
    ) -> Dict[str, float]:
        """測試長期趨勢穩定性"""
        window_size = self.config.rolling_window_size
        if len(data) < window_size * 2:
            return {}

        trend_metrics = {}
        rolling_performances = []

        # 滾動窗口分析
        for i in range(0, len(data) - window_size + 1, window_size // 4):
            window_data = data.iloc[i:i + window_size]

            try:
                strategy_params = self._convert_parameters(params, strategy_type)
                result = self.vectorbt_engine.backtest_strategy(
                    data=window_data,
                    strategy=self._get_strategy_name(strategy_type),
                    parameters=strategy_params,
                    symbol="0700.HK"
                )

                rolling_performances.append(result.sharpe_ratio)

            except Exception:
                continue

        if len(rolling_performances) >= 3:
            # 計算趨勢穩定性
            sharpe_trend = np.polyfit(range(len(rolling_performances)), rolling_performances, 1)[0]
            trend_consistency = 1 - abs(sharpe_trend) / np.mean(np.abs(rolling_performances)) if np.mean(np.abs(rolling_performances)) > 0 else 0

            trend_metrics.update({
                'long_term_sharpe_trend': sharpe_trend,
                'trend_consistency': trend_consistency,
                'rolling_performance_variance': np.var(rolling_performances)
            })

        return trend_metrics

    def _perform_sensitivity_analysis(
        self,
        params: Dict[str, Any],
        strategy_type: str,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """參數敏感性分析"""
        logger.info("Performing sensitivity analysis...")

        sensitivity_results = {}
        base_params = self._convert_parameters(params, strategy_type)

        # 獲取基準性能
        try:
            base_result = self.vectorbt_engine.backtest_strategy(
                data=data,
                strategy=self._get_strategy_name(strategy_type),
                parameters=base_params,
                symbol="0700.HK"
            )
            base_sharpe = base_result.sharpe_ratio
        except Exception as e:
            logger.error(f"Base case failed for sensitivity analysis: {e}")
            return {}

        # 分析每個參數的敏感性
        for param_name, param_value in base_params.items():
            if isinstance(param_value, (int, float)):
                sensitivity = self._analyze_parameter_sensitivity(
                    base_params, param_name, param_value, data, strategy_type, base_sharpe
                )
                sensitivity_results[param_name] = sensitivity

        # 整體敏感性分析
        overall_sensitivity = self._calculate_overall_sensitivity(sensitivity_results)

        return {
            'parameter_sensitivities': sensitivity_results,
            'overall_sensitivity': overall_sensitivity,
            'robust_parameters': [k for k, v in sensitivity_results.items() if v.get('sensitivity_score', 1.0) < 0.5]
        }

    def _analyze_parameter_sensitivity(
        self,
        base_params: Dict[str, Any],
        param_name: str,
        param_value: Union[int, float],
        data: pd.DataFrame,
        strategy_type: str,
        base_sharpe: float
    ) -> Dict[str, Any]:
        """分析單個參數的敏感性"""
        step_size = self.config.sensitivity_step_sizes.get(param_name, param_value * 0.1)
        test_values = []

        # 生成測試值（±10%, ±20%）
        for multiplier in [0.8, 0.9, 1.1, 1.2]:
            if param_name in ['period', 'fast', 'slow']:  # 整數參數
                test_value = int(param_value * multiplier)
                test_value = max(1, test_value)  # 確保最小值為1
            else:
                test_value = param_value * multiplier

            test_values.append(test_value)

        sensitivity_scores = []

        for test_value in test_values:
            test_params = base_params.copy()
            test_params[param_name] = test_value

            try:
                result = self.vectorbt_engine.backtest_strategy(
                    data=data,
                    strategy=self._get_strategy_name(strategy_type),
                    parameters=test_params,
                    symbol="0700.HK"
                )

                # 計算性能變化
                sharpe_change = abs(result.sharpe_ratio - base_sharpe) / abs(base_sharpe) if base_sharpe != 0 else 1.0
                sensitivity_scores.append(sharpe_change)

            except Exception:
                sensitivity_scores.append(1.0)  # 最大懲罰

        # 計算敏感性指標
        avg_sensitivity = np.mean(sensitivity_scores)
        max_sensitivity = np.max(sensitivity_scores)

        return {
            'base_value': param_value,
            'step_size': step_size,
            'test_values': test_values,
            'sensitivity_scores': sensitivity_scores,
            'average_sensitivity': avg_sensitivity,
            'max_sensitivity': max_sensitivity,
            'sensitivity_score': avg_sensitivity,  # 綜合敏感性評分
            'is_stable': avg_sensitivity < 0.3  # 敏感性閾值
        }

    def _calculate_overall_sensitivity(self, sensitivity_results: Dict[str, Any]) -> float:
        """計算整體敏感性評分"""
        if not sensitivity_results:
            return 1.0

        sensitivity_scores = [
            result.get('average_sensitivity', 1.0) for result in sensitivity_results.values()
        ]

        return np.mean(sensitivity_scores)

    def _perform_out_of_sample_test(
        self,
        params: Dict[str, Any],
        strategy_type: str,
        data: pd.DataFrame
    ) -> Dict[str, float]:
        """樣本外測試"""
        logger.info("Performing out-of-sample testing...")

        # 分割數據
        split_point = int(len(data) * (1 - self.config.out_of_sample_ratio))
        train_data = data.iloc[:split_point]
        test_data = data.iloc[split_point:]

        if len(test_data) < self.config.min_test_period:
            return {'error': 'Insufficient out-of-sample data'}

        try:
            # 訓練期性能
            train_params = self._convert_parameters(params, strategy_type)
            train_result = self.vectorbt_engine.backtest_strategy(
                data=train_data,
                strategy=self._get_strategy_name(strategy_type),
                parameters=train_params,
                symbol="0700.HK"
            )

            # 測試期性能（使用相同參數）
            test_result = self.vectorbt_engine.backtest_strategy(
                data=test_data,
                strategy=self._get_strategy_name(strategy_type),
                parameters=train_params,
                symbol="0700.HK"
            )

            # 計算性能指標
            train_sharpe = train_result.sharpe_ratio
            test_sharpe = test_result.sharpe_ratio

            performance_degradation = (train_sharpe - test_sharpe) / abs(train_sharpe) if train_sharpe != 0 else 1.0

            return {
                'train_sharpe': train_sharpe,
                'test_sharpe': test_sharpe,
                'performance_degradation': performance_degradation,
                'performance_consistency': 1 - performance_degradation,
                'train_return': train_result.total_return,
                'test_return': test_result.total_return,
                'train_drawdown': train_result.max_drawdown,
                'test_drawdown': test_result.max_drawdown,
                'out_of_sample_valid': performance_degradation < 0.5  # 性能下降小於50%
            }

        except Exception as e:
            logger.error(f"Out-of-sample test failed: {e}")
            return {'error': str(e)}

    def _perform_walk_forward_analysis(
        self,
        params: Dict[str, Any],
        strategy_type: str,
        data: pd.DataFrame
    ) -> Dict[str, Any]:
        """前向分析（Walk Forward Analysis）"""
        logger.info("Performing walk-forward analysis...")

        if len(data) < self.config.min_test_period * self.config.walk_forward_windows:
            return {'error': 'Insufficient data for walk-forward analysis'}

        walk_forward_results = []
        window_size = len(data) // self.config.walk_forward_windows

        for i in range(self.config.walk_forward_windows):
            start_idx = i * (len(data) - window_size) // (self.config.walk_forward_windows - 1) if self.config.walk_forward_windows > 1 else 0
            end_idx = start_idx + window_size

            if end_idx >= len(data):
                end_idx = len(data) - 1
                start_idx = max(0, end_idx - window_size)

            train_data = data.iloc[start_idx:end_idx]
            test_data = data.iloc[end_idx:min(end_idx + window_size // 2, len(data))]

            if len(test_data) < self.config.min_test_period // 2:
                continue

            try:
                strategy_params = self._convert_parameters(params, strategy_type)

                # 訓練期
                train_result = self.vectorbt_engine.backtest_strategy(
                    data=train_data,
                    strategy=self._get_strategy_name(strategy_type),
                    parameters=strategy_params,
                    symbol="0700.HK"
                )

                # 測試期
                test_result = self.vectorbt_engine.backtest_strategy(
                    data=test_data,
                    strategy=self._get_strategy_name(strategy_type),
                    parameters=strategy_params,
                    symbol="0700.HK"
                )

                walk_forward_results.append({
                    'fold': i + 1,
                    'train_period': f"{train_data.index[0].strftime('%Y-%m-%d')} to {train_data.index[-1].strftime('%Y-%m-%d')}",
                    'test_period': f"{test_data.index[0].strftime('%Y-%m-%d')} to {test_data.index[-1].strftime('%Y-%m-%d')}",
                    'train_sharpe': train_result.sharpe_ratio,
                    'test_sharpe': test_result.sharpe_ratio,
                    'train_return': train_result.total_return,
                    'test_return': test_result.total_return,
                    'performance_ratio': test_result.sharpe_ratio / train_result.sharpe_ratio if train_result.sharpe_ratio != 0 else 0
                })

            except Exception as e:
                logger.warning(f"Walk-forward fold {i+1} failed: {e}")
                continue

        if walk_forward_results:
            train_sharpes = [r['train_sharpe'] for r in walk_forward_results]
            test_sharpes = [r['test_sharpe'] for r in walk_forward_results]
            performance_ratios = [r['performance_ratio'] for r in walk_forward_results]

            return {
                'fold_results': walk_forward_results,
                'avg_train_sharpe': np.mean(train_sharpes),
                'avg_test_sharpe': np.mean(test_sharpes),
                'avg_performance_ratio': np.mean(performance_ratios),
                'performance_consistency': 1 - np.std(performance_ratios),
                'positive_performance_folds': len([r for r in performance_ratios if r > 0.8]),
                'walk_forward_valid': np.mean(performance_ratios) > 0.6
            }
        else:
            return {'error': 'No successful walk-forward folds'}

    def _convert_parameters(self, params: Dict[str, Any], strategy_type: str) -> Dict[str, Any]:
        """轉換參數格式"""
        if strategy_type == "HIBOR_RSI":
            return {
                'period': params.get('rsi_period', params.get('period', 14)),
                'oversold': params.get('rsi_oversold', params.get('oversold', 30)),
                'overbought': params.get('rsi_overbought', params.get('overbought', 70))
            }
        elif strategy_type == "MONETARY_MACD":
            return {
                'fast': params.get('macd_fast', params.get('fast', 12)),
                'slow': params.get('macd_slow', params.get('slow', 26)),
                'signal': params.get('macd_signal', params.get('signal', 9))
            }
        else:
            return params

    def _get_strategy_name(self, strategy_type: str) -> str:
        """獲取策略名稱"""
        strategy_map = {
            'HIBOR_RSI': 'RSI_MEAN_REVERSION',
            'MONETARY_MACD': 'MACD_CROSSOVER'
        }
        return strategy_map.get(strategy_type, strategy_type)

    def _calculate_overall_stability_score(
        self,
        time_stability: Dict[str, float],
        sensitivity_analysis: Dict[str, Any],
        out_of_sample_test: Dict[str, float],
        walk_forward_test: Dict[str, Any]
    ) -> float:
        """計算總體穩定性評分"""
        scores = []

        # 時間穩定性評分（權重30%）
        if 'sharpe_stability' in time_stability:
            time_score = time_stability['sharpe_stability'] * 100
            scores.append(('time_stability', time_score, 0.3))

        # 敏感性評分（權重25%）
        overall_sensitivity = sensitivity_analysis.get('overall_sensitivity', 1.0)
        sensitivity_score = (1 - min(overall_sensitivity, 1.0)) * 100
        scores.append(('sensitivity', sensitivity_score, 0.25))

        # 樣本外評分（權重25%）
        if 'performance_consistency' in out_of_sample_test:
            oos_score = out_of_sample_test['performance_consistency'] * 100
            scores.append(('out_of_sample', oos_score, 0.25))

        # 前向分析評分（權重20%）
        if 'performance_consistency' in walk_forward_test:
            wf_score = walk_forward_test['performance_consistency'] * 100
            scores.append(('walk_forward', wf_score, 0.2))

        # 計算加權平均
        if scores:
            weighted_score = sum(score * weight for _, score, weight in scores)
            return max(0, min(100, weighted_score))
        else:
            return 0

    def _generate_stability_recommendations(
        self,
        time_stability: Dict[str, float],
        sensitivity_analysis: Dict[str, Any],
        out_of_sample_test: Dict[str, float],
        walk_forward_test: Dict[str, Any]
    ) -> List[str]:
        """生成穩定性建議"""
        recommendations = []

        # 時間穩定性建議
        if time_stability.get('sharpe_stability', 0) < 0.5:
            recommendations.append("時間穩定性較低，建議增加市場 regime 檢測")
            recommendations.append("考慮實施動態參數調整機制")

        if time_stability.get('positive_periods_ratio', 1) < 0.6:
            recommendations.append("正收益期比例偏低，建議優化進場條件")

        # 敏感性建議
        robust_params = sensitivity_analysis.get('robust_parameters', [])
        if len(robust_params) < len(sensitivity_analysis.get('parameter_sensitivities', {})):
            recommendations.append("部分參數過於敏感，建議擴大參數容錯範圍")

        overall_sensitivity = sensitivity_analysis.get('overall_sensitivity', 0)
        if overall_sensitivity > 0.5:
            recommendations.append("整體參數敏感性偏高，建議簡化策略邏輯")

        # 樣本外測試建議
        if out_of_sample_test.get('performance_degradation', 1) > 0.5:
            recommendations.append("樣本外性能下降顯著，可能存在過度擬合")

        if not out_of_sample_test.get('out_of_sample_valid', True):
            recommendations.append("樣本外測試未通過，建議重新優化參數")

        # 前向分析建議
        if walk_forward_test.get('avg_performance_ratio', 0) < 0.7:
            recommendations.append("前向分析性能比率偏低，策略穩定性有待提升")

        if walk_forward_test.get('positive_performance_folds', 0) < walk_forward_test.get('fold_results', [{}]).__len__() // 2:
            recommendations.append("前向分析正向性能期數不足，建議增加適應性機制")

        # 通用建議
        if not recommendations:
            recommendations.append("參數穩定性良好，可進行實盤測試")

        return recommendations

    def _analyze_overall_stability(self, validation_results: List[StabilityResult]) -> Dict[str, Any]:
        """分析整體穩定性結果"""
        if not validation_results:
            return {'error': 'No validation results available'}

        stability_scores = [r.overall_stability_score for r in validation_results]
        stable_count = len([r for r in validation_results if r.overall_stability_score >= 70])

        # 分析最穩定參數的共同特徵
        stable_params = [r for r in validation_results if r.overall_stability_score >= 70]

        return {
            'total_validated': len(validation_results),
            'stable_parameters': stable_count,
            'stability_ratio': stable_count / len(validation_results),
            'average_stability_score': np.mean(stability_scores),
            'stability_score_std': np.std(stability_scores),
            'best_stability_score': np.max(stability_scores),
            'worst_stability_score': np.min(stability_scores),
            'stability_distribution': {
                'excellent (>90)': len([r for r in validation_results if r.overall_stability_score > 90]),
                'good (70-90)': len([r for r in validation_results if 70 <= r.overall_stability_score <= 90]),
                'fair (50-70)': len([r for r in validation_results if 50 <= r.overall_stability_score < 70]),
                'poor (<50)': len([r for r in validation_results if r.overall_stability_score < 50])
            },
            'common_issues': self._identify_common_stability_issues(validation_results)
        }

    def _identify_common_stability_issues(self, validation_results: List[StabilityResult]) -> List[str]:
        """識別常見穩定性問題"""
        issues = []

        # 檢查時間穩定性問題
        time_issues = [r for r in validation_results if r.time_stability_metrics.get('sharpe_stability', 1) < 0.5]
        if len(time_issues) > len(validation_results) * 0.5:
            issues.append("時間穩定性問題：超過50%的參數在時間窗口中表現不穩定")

        # 檢查敏感性問題
        sensitivity_issues = [r for r in validation_results if r.sensitivity_metrics.get('overall_sensitivity', 0) > 0.5]
        if len(sensitivity_issues) > len(validation_results) * 0.5:
            issues.append("參數敏感性问题：超過50%的參數對微小變化過於敏感")

        # 檢查樣本外問題
        oos_issues = [r for r in validation_results if not r.out_of_sample_performance.get('out_of_sample_valid', True)]
        if len(oos_issues) > len(validation_results) * 0.5:
            issues.append("樣本外表現問題：超過50%的參數在樣本外測試中表現不佳")

        # 檢查前向分析問題
        wf_issues = [r for r in validation_results if not r.walk_forward_results.get('walk_forward_valid', True)]
        if len(wf_issues) > len(validation_results) * 0.5:
            issues.append("前向分析問題：超過50%的參數在前向分析中表現不穩定")

        return issues

    def save_validation_results(self, results: Dict[str, Any], filename: str) -> None:
        """保存驗證結果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"parameter_stability_validation_{filename}_{timestamp}.json"

        # 添加驗證統計
        results['validation_statistics'] = self.validation_stats

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Stability validation results saved to: {output_file}")

    def get_validation_summary(self) -> Dict[str, Any]:
        """獲取驗證總結"""
        return {
            'validation_statistics': self.validation_stats,
            'configuration': {
                'min_test_period': self.config.min_test_period,
                'validation_windows': self.config.validation_windows,
                'sharpe_stability_threshold': self.config.sharpe_stability_threshold,
                'performance_correlation_threshold': self.config.performance_correlation_threshold,
                'out_of_sample_ratio': self.config.out_of_sample_ratio,
                'walk_forward_windows': self.config.walk_forward_windows
            }
        }

# 便利函數
def quick_stability_validation(
    optimal_parameters: List[Dict[str, Any]],
    strategy_type: str,
    symbol: str = "0700.HK"
) -> Dict[str, Any]:
    """
    快速參數穩定性驗證

    Args:
        optimal_parameters: 最優參數列表
        strategy_type: 策略類型
        symbol: 股票代碼

    Returns:
        驗證結果
    """
    validator = ParameterStabilityValidator()

    # 只驗證前5個最優參數以提高效率
    top_parameters = optimal_parameters[:5]

    results = validator.validate_parameter_stability(
        top_parameters, strategy_type, symbol, data_period=365
    )

    # 保存結果
    validator.save_validation_results(results, f"{strategy_type}_quick")

    return results

if __name__ == "__main__":
    # 示例用法
    print("參數穩定性驗證系統已就緒")
    print("使用 quick_stability_validation() 函數進行快速驗證")