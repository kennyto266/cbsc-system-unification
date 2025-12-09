#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高級統計驗證框架 - 提供嚴格的統計驗證和穩定性分析
Advanced Statistical Validation Framework - Provides rigorous statistical validation and stability analysis

實現樣本外驗證、統計顯著性檢驗、參數穩定性分析和風險評估
"""

import numpy as np
import pandas as pd
import logging
import time
from typing import Dict, List, Tuple, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from scipy import stats
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """驗證結果"""
    test_name: str
    test_type: str  # 'significance', 'stability', 'out_of_sample', 'sensitivity'
    statistic_value: float
    p_value: float
    critical_value: float
    is_significant: bool
    confidence_level: float
    effect_size: Optional[float] = None
    interpretation: str = ""
    timestamp: float = field(default_factory=time.time)

@dataclass
class ParameterStabilityResult:
    """參數穩定性結果"""
    parameter_name: str
    parameter_value: float
    stability_score: float  # 0-1, 越高越穩定
    variance_coefficient: float
    temporal_consistency: float
    sensitivity_score: float
    robust_range: Tuple[float, float] = (0.0, 0.0)
    recommendation: str = ""

@dataclass
class OutOfSampleValidationResult:
    """樣本外驗證結果"""
    in_sample_sharpe: float
    out_of_sample_sharpe: float
    performance_degradation: float
    degradation_percentage: float
    is_valid: bool
    overfitting_score: float  # 0-1, 越高越過度擬合
    validation_periods: List[str] = field(default_factory=list)

@dataclass
class StatisticalReport:
    """統計驗證報告"""
    validator_id: str
    timestamp: float
    validation_results: List[ValidationResult]
    stability_analysis: Dict[str, ParameterStabilityResult]
    out_of_sample_results: List[OutOfSampleValidationResult]
    risk_metrics: Dict[str, float]
    recommendations: List[str]
    overall_assessment: str

class AdvancedStatisticalValidator:
    """
    高級統計驗證器

    實現：
    - 樣本外驗證 (K-fold, 時間序列交叉驗證)
    - 統計顯著性檢驗 (t檢驗, Wilcoxon, KS檢驗)
    - 參數穩定性分析
    - 過度擬合檢測
    - 風險評估和壓力測試
    """

    def __init__(self,
                 confidence_level: float = 0.95,
                 significance_level: float = 0.05,
                 min_samples: int = 30):
        """
        初始化高級統計驗證器

        Args:
            confidence_level: 置信水平
            significance_level: 顯著性水平
            min_samples: 最小樣本數量
        """
        self.confidence_level = confidence_level
        self.significance_level = significance_level
        self.min_samples = min_samples

        # 臨界值表
        self.critical_values = self._initialize_critical_values()

        # 驗證歷史
        self.validation_history = []

        logger.info("Advanced Statistical Validator initialized")

    def _initialize_critical_values(self) -> Dict[str, Dict[int, float]]:
        """初始化臨界值表"""
        # t檢驗臨界值
        t_critical = {}
        for df in [10, 20, 30, 50, 100, 200, 500, 1000]:
            t_critical[df] = {
                'two_tail': stats.t.ppf(1 - self.significance_level/2, df),
                'one_tail': stats.t.ppf(1 - self.significance_level, df)
            }

        # Wilcoxon符號秩檢驗臨界值
        wilcoxon_critical = {}
        for n in [10, 20, 30, 50, 100]:
            wilcoxon_critical[n] = stats.wilcoxon.ppf(1 - self.significance_level, n)

        return {
            't_test': t_critical,
            'wilcoxon': wilcoxon_critical
        }

    def validate_out_of_sample_performance(self,
                                         in_sample_returns: pd.Series,
                                         out_of_sample_returns: pd.Series,
                                         strategy_name: str = "unknown") -> OutOfSampleValidationResult:
        """
        驗證樣本外性能

        Args:
            in_sample_returns: 樣本內回報序列
            out_of_sample_returns: 樣本外回報序列
            strategy_name: 策略名稱

        Returns:
            樣本外驗證結果
        """
        logger.info(f"Validating out-of-sample performance for {strategy_name}")

        try:
            # 計算Sharpe比率 (3%無風險利率)
            def calculate_sharpe(returns):
                risk_free_rate = 0.03
                excess_returns = returns - risk_free_rate / 252  # 日化
                return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0

            in_sample_sharpe = calculate_sharpe(in_sample_returns)
            out_of_sample_sharpe = calculate_sharpe(out_of_sample_returns)

            # 計算性能下降
            if in_sample_sharpe != 0:
                performance_degradation = in_sample_sharpe - out_of_sample_sharpe
                degradation_percentage = (performance_degradation / abs(in_sample_sharpe)) * 100
            else:
                performance_degradation = 0.0
                degradation_percentage = 0.0

            # 評估過度擬合分數
            overfitting_score = max(0.0, min(1.0, degradation_percentage / 50.0))

            # 驗證標準
            is_valid = degradation_percentage < 20.0  # 性能下降不超過20%
            if degradation_percentage < 5.0:
                validation_status = "Excellent"
            elif degradation_percentage < 15.0:
                validation_status = "Good"
            else:
                validation_status = "Poor"

            result = OutOfSampleValidationResult(
                in_sample_sharpe=in_sample_sharpe,
                out_of_sample_sharpe=out_of_sample_sharpe,
                performance_degradation=performance_degradation,
                degradation_percentage=degradation_percentage,
                is_valid=is_valid,
                overfitting_score=overfitting_score,
                validation_periods=[f"Period_{i+1}" for i in range(1)],  # 簡化
                interpretation=f"Out-of-sample validation: {validation_status}"
            )

            logger.info(f"Out-of-sample validation completed - "
                       f"In-sample Sharpe: {in_sample_sharpe:.3f}, "
                       f"Out-of-sample Sharpe: {out_of_sample_sharpe:.3f}, "
                       f"Degradation: {degradation_percentage:.1f}%")

            return result

        except Exception as e:
            logger.error(f"Error in out-of-sample validation: {e}")
            return OutOfSampleValidationResult(0, 0, 0, 0, False, 1.0, [])

    def perform_k_fold_cross_validation(self,
                                         data: pd.DataFrame,
                                         strategy_func: Callable,
                                         parameters: Dict[str, Any],
                                         n_folds: int = 5) -> Dict[str, Any]:
        """
        執行K折交叉驗證

        Args:
            data: 數據
            strategy_func: 策略函數
            parameters: 策略參數
            n_folds: 折數

        Returns:
            交叉驗證結果
        """
        logger.info(f"Performing {n_folds}-fold cross-validation")

        try:
            if len(data) < n_folds * self.min_samples:
                logger.warning(f"Insufficient data for {n_folds}-fold CV: {len(data)} < {n_folds * self.min_samples}")
                return {'error': 'Insufficient data'}

            # 創建折數
            fold_size = len(data) // n_folds
            fold_results = []

            for fold in range(n_folds):
                # 分割數據
                start_idx = fold * fold_size
                end_idx = start_idx + fold_size if fold < n_folds - 1 else len(data)

                train_data = data.drop(data.index[start_idx:end_idx])
                test_data = data.iloc[start_idx:end_idx]

                # 執行策略
                train_result = strategy_func(train_data, parameters)
                test_result = strategy_func(test_data, parameters)

                # 計算性能指標
                train_sharpe = self._calculate_sharpe_from_result(train_result)
                test_sharpe = self._calculate_sharpe_from_result(test_result)

                fold_results.append({
                    'fold': fold + 1,
                    'train_sharpe': train_sharpe,
                    'test_sharpe': test_sharpe,
                    'train_size': len(train_data),
                    'test_size': len(test_data)
                })

            # 計算交叉驗證統計
            train_sharpes = [r['train_sharpe'] for r in fold_results]
            test_sharpes = [r['test_sharpe'] for r in fold_results]

            cv_mean = np.mean(test_sharpes)
            cv_std = np.std(test_sharpes)
            cv_range = (min(test_sharpes), max(test_sharpes))

            # 計算95%置信區間
            sem = cv_std / np.sqrt(n_folds)
            confidence_interval = (cv_mean - 1.96 * sem, cv_mean + 1.96 * sem)

            # 評估交叉驗證穩定性
            cv_cv_ratio = cv_std / abs(cv_mean) if cv_mean != 0 else float('inf')
            stability_score = max(0, 1 - cv_cv_ratio)

            result = {
                'n_folds': n_folds,
                'fold_results': fold_results,
                'statistics': {
                    'mean_sharpe': cv_mean,
                    'std_sharpe': cv_std,
                    'range_sharpe': cv_range,
                    'confidence_interval': confidence_interval,
                    'stability_score': stability_score
                },
                'validation_result': self._create_validation_result(
                    'k_fold_cv',
                    cv_mean,
                    cv_std,
                    n_folds - 1
                )
            }

            logger.info(f"K-fold CV completed - "
                       f"Mean Sharpe: {cv_mean:.3f}, "
                       f"Std: {cv_std:.3f}, "
                       f"Stability: {stability_score:.3f}")

            return result

        except Exception as e:
            logger.error(f"Error in K-fold cross-validation: {e}")
            return {'error': str(e)}

    def perform_time_series_cross_validation(self,
                                             data: pd.DataFrame,
                                             strategy_func: Callable,
                                             parameters: Dict[str, Any],
                                             window_size: int = 252,
                                             n_splits: int = 5) -> Dict[str, Any]:
        """
        執行時間序列交叉驗證（滾動窗口）

        Args:
            data: 時序數據
            strategy_func: 策略函數
            parameters: 策略參數
            window_size: 窗口大小
            n_splits: 分割數

        Returns:
            時序交叉驗證結果
        """
        logger.info(f"Performing time series cross-validation "
                   f"(window: {window_size}, splits: {n_splits})")

        try:
            if len(data) < window_size * n_splits:
                logger.warning(f"Insufficient data for TS CV: {len(data)} < {window_size * n_splits}")
                return {'error': 'Insufficient data'}

            split_size = window_size
            results = []

            for split in range(n_splits):
                # 定義訓練和測試期間
                test_start = split * split_size
                test_end = test_start + split_size

                train_data = data.iloc[:test_start]
                test_data = data.iloc[test_start:test_end]

                # 執行策略
                train_result = strategy_func(train_data, parameters)
                test_result = strategy_func(test_data, parameters)

                # 計算性能指標
                train_sharpe = self._calculate_sharpe_from_result(train_result)
                test_sharpe = self._calculate_sharpe_from_result(test_result)

                results.append({
                    'split': split + 1,
                    'train_period': f"1-{test_start}",
                    'test_period': f"{test_start + 1}-{test_end}",
                    'train_sharpe': train_sharpe,
                    'test_sharpe': test_sharpe,
                    'train_size': len(train_data),
                    'test_size': len(test_data)
                })

            # 計算統計
            test_sharpes = [r['test_sharpe'] for r in results]
            mean_sharpe = np.mean(test_sharpes)
            std_sharpe = np.std(test_sharpes)

            # 計算時間序列穩定性
            ts_stability = self._calculate_time_series_stability(test_sharpes)

            result = {
                'window_size': window_size,
                'n_splits': n_splits,
                'results': results,
                'statistics': {
                    'mean_sharpe': mean_sharpe,
                    'std_sharpe': std_sharpe,
                    'range_sharpe': (min(test_sharpes), max(test_sharpe)),
                    'ts_stability_score': ts_stability
                },
                'validation_result': self._create_validation_result(
                    'time_series_cv',
                    mean_sharpe,
                    std_sharpe,
                    n_splits - 1
                )
            }

            logger.info(f"Time series CV completed - "
                       f"Mean Sharpe: {mean_sharpe:.3f}, "
                       f"TS Stability: {ts_stability:.3f}")

            return result

        except Exception as e:
            logger.error(f"Error in time series cross-validation: {e}")
            return {'error': str(e)}

    def perform_statistical_significance_test(self,
                                                benchmark_returns: pd.Series,
                                                strategy_returns: pd.Series,
                                                test_type: str = 'paired_t') -> ValidationResult:
        """
        執行統計顯著性檢驗

        Args:
            benchmark_returns: 基準回報序列
            strategy_returns: 策略回報序列
            test_type: 檢驗類型 ('paired_t', 'wilcoxon', 'ks')

        Returns:
            驗證結果
        """
        logger.info(f"Performing {test_type} significance test")

        try:
            # 確保數據長度一致
            min_len = min(len(benchmark_returns), len(strategy_returns))
            benchmark_aligned = benchmark_returns.iloc[-min_len:]
            strategy_aligned = strategy_returns.iloc[-min_len:]

            if test_type == 'paired_t':
                result = self._paired_t_test(benchmark_aligned, strategy_aligned)
            elif test_type == 'wilcoxon':
                result = self._wilcoxon_test(benchmark_aligned, strategy_aligned)
            elif test_type == 'ks':
                result = self._kolmogorov_smirnov_test(benchmark_aligned, strategy_aligned)
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            logger.info(f"{test_type} test completed - "
                       f"Statistic: {result.statistic_value:.4f}, "
                       f"P-value: {result.p_value:.4f}, "
                       f"Significant: {result.is_significant}")

            return result

        except Exception as e:
            logger.error(f"Error in significance test: {e}")
            return ValidationResult(
                test_name=test_type,
                test_type='significance',
                statistic_value=0.0,
                p_value=1.0,
                critical_value=0.0,
                is_significant=False,
                confidence_level=self.confidence_level,
                interpretation=f"Error: {e}"
            )

    def _paired_t_test(self, benchmark_returns: pd.Series, strategy_returns: pd.Series) -> ValidationResult:
        """配對t檢驗"""
        if len(benchmark_returns) < 2:
            raise ValueError("Insufficient data for paired t-test")

        # 計算差值
        differences = strategy_returns - benchmark_returns

        # 執行t檢驗
        t_stat, p_value = stats.ttest_1samp(differences, 0)

        # 獲取臨界值
        df = len(differences) - 1
        critical_value = self.critical_values['t_test'][df]['two_tail']

        # 判斷顯著性
        is_significant = abs(t_stat) > critical_value
        effect_size = np.mean(differences) / (np.std(differences) + 1e-10)

        # 解釋結果
        if is_significant and effect_size > 0:
            interpretation = "Strategy significantly outperforms benchmark with medium to large effect size"
        elif is_significant and effect_size <= 0:
            interpretation = "Strategy significantly underperforms benchmark with medium to large effect size"
        else:
            interpretation = "No statistically significant difference between strategy and benchmark"

        return ValidationResult(
            test_name='paired_t_test',
            test_type='significance',
            statistic_value=t_stat,
            p_value=p_value,
            critical_value=critical_value,
            is_significant=is_significant,
            confidence_level=self.confidence_level,
            effect_size=effect_size,
            interpretation=interpretation
        )

    def _wilcoxon_test(self, benchmark_returns: pd.Series, strategy_returns: pd.Series) -> ValidationResult:
        """Wilcoxon符號秩檢驗"""
        # 計算差值
        differences = strategy_returns - benchmark_returns

        # 執行Wilcoxon檢驗
        stat, p_value = stats.wilcoxon(differences)

        # 獲取臨界值
        n = len(differences)
        critical_value = self.critical_values['wilcoxon'].get(n, 2.576)

        # 判斷顯著性
        is_significant = abs(stat) > critical_value
        effect_size = np.median(differences) / (np.median(np.abs(differences)) + 1e-10)

        # 解釋結果
        if is_significant:
            interpretation = "Statistically significant difference detected (non-parametric test)"
        else:
            interpretation = "No statistically significant difference detected"

        return ValidationResult(
            test_name='wilcoxon_test',
            test_type='significance',
            statistic_value=stat,
            p_value=p_value,
            critical_value=critical_value,
            is_significant=is_significant,
            confidence_level=self.confidence_level,
            effect_size=effect_size,
            interpretation=interpretation
        )

    def _kolmogorov_smirnov_test(self, benchmark_returns: pd.Series, strategy_returns: pd.Series) -> ValidationResult:
        """Kolmogorov-Smirnov檢驗"""
        try:
            # 執行KS檢驗
            stat, p_value = stats.ks_2samp(benchmark_returns, strategy_returns)

            # 解釋結果
            if p_value < self.significance_level:
                interpretation = "Distributions differ significantly"
            else:
                interpretation = "No significant distribution difference detected"

            return ValidationResult(
                test_name='kolmogorov_smirnov_test',
                test_type='significance',
                statistic_value=stat,
                p_value=p_value,
                critical_value=0.0,  # KS檢驗不使用固定臨界值
                is_significant=p_value < self.significance_level,
                confidence_level=self.confidence_level,
                interpretation=interpretation
            )

        except Exception as e:
            logger.error(f"Error in KS test: {e}")
            return ValidationResult(
                test_name='kolmogorov_smirnov_test',
                test_type='significance',
                statistic_value=0.0,
                p_value=1.0,
                critical_value=0.0,
                is_significant=False,
                confidence_level=self.confidence_level,
                interpretation=f"Error: {e}"
            )

    def analyze_parameter_stability(self,
                                    parameter_history: List[Dict[str, Any]],
                                    performance_history: List[float]) -> Dict[str, ParameterStabilityResult]:
        """
        分析參數穩定性

        Args:
            parameter_history: 參數歷史
            performance_history: 對應的性能歷史

        Returns:
            參數穩定性分析結果
        """
        logger.info(f"Analyzing parameter stability for {len(parameter_history)} parameter sets")

        try:
            if not parameter_history:
                return {}

            stability_results = {}
            parameter_names = list(parameter_history[0].keys()) if parameter_history else []

            for param_name in parameter_names:
                # 提取參數序列
                param_values = [params[param_name] for params in parameter_history]

                # 計算統計指標
                mean_val = np.mean(param_values)
                std_val = np.std(param_values)
                var_coefficient = std_val / (abs(mean_val) + 1e-10)

                # 時序一致性（趨勢相關係數）
                temporal_consistency = self._calculate_temporal_consistency(param_values)

                # 敏感度分析
                sensitivity_score = self._calculate_parameter_sensitivity(
                    param_values, performance_history
                )

                # 魯棒區間（基於標準差）
                robust_lower = mean_val - 2 * std_val
                robust_upper = mean_val + 2 * std_val

                # 穩定性評分 (0-1)
                stability_score = self._calculate_stability_score(
                    var_coefficient, temporal_consistency, sensitivity_score
                )

                # 生成建議
                if stability_score > 0.8:
                    recommendation = "Parameter is highly stable"
                elif stability_score > 0.6:
                    recommendation = "Parameter is moderately stable"
                elif stability_score > 0.4:
                    recommendation = "Parameter shows some instability, consider re-optimization"
                else:
                    recommendation = "Parameter is unstable, requires investigation"

                stability_results[param_name] = ParameterStabilityResult(
                    parameter_name=param_name,
                    parameter_value=mean_val,
                    stability_score=stability_score,
                    variance_coefficient=var_coefficient,
                    temporal_consistency=temporal_consistency,
                    sensitivity_score=sensitivity_score,
                    robust_range=(robust_lower, robust_upper),
                    recommendation=recommendation
                )

            logger.info(f"Parameter stability analysis completed for {len(stability_results)} parameters")

            return stability_results

        except Exception as e:
            logger.error(f"Error in parameter stability analysis: {e}")
            return {}

    def _calculate_temporal_consistency(self, values: List[float]) -> float:
        """計算時序一致性（趨勢相關係數）"""
        if len(values) < 2:
            return 0.0

        try:
            # 計算一階差分
            diffs = np.diff(values)

            # 計算自相關
            if len(diffs) < 2:
                return 0.0

            # 簡化版本：使用差分自相關
            autocorr = np.correlate(diffs[:-1], diffs[1:])
            return max(0.0, autocorr) if not np.isnan(autocorr) else 0.0

        except Exception:
            return 0.0

    def _calculate_parameter_sensitivity(self,
                                    param_values: List[float],
                                    performance_values: List[float]) -> float:
        """計算參數敏感度"""
        if len(param_values) != len(performance_values):
            return 0.0

        try:
            # 計算相關係數
            correlation = np.corrcoef(param_values, performance_values)[0, 1]
            return abs(correlation) if not np.isnan(correlation) else 0.0

        except Exception:
            return 0.0

    def _calculate_stability_score(self,
                                var_coefficient: float,
                                temporal_consistency: float,
                                sensitivity_score: float) -> float:
        """計算綜合穩定性評分"""
        # 加權組合各項指標
        # 低變異係數 + 高時序一致性 + 低敏感度 = 高穩定性

        # 變異係數 (0-1, 越低越好)
        var_score = max(0, 1 - var_coefficient)

        # 時序一致性 (0-1, 越高越好)
        temporal_score = temporal_consistency

        # 敏感度 (0-1, 越低越好)
        sensitivity_score = max(0, 1 - sensitivity_score)

        # 加權組合
        return (var_score * 0.4 + temporal_score * 0.3 + sensitivity_score * 0.3)

    def _calculate_sharpe_from_result(self, result: Dict[str, Any]) -> float:
        """從結果對象計算Sharpe比率"""
        try:
            # 嘗試從結果中提取Sharpe比率
            if 'sharpe_ratio' in result:
                return float(result['sharpe_ratio'])
            elif 'total_return' in result and 'max_drawdown' in result:
                # 計算簡化Sharpe比率
                total_return = float(result['total_return'])
                max_drawdown = float(result['max_drawdown'])
                if max_drawdown != 0:
                    return (total_return - 0.03) / abs(max_drawdown)  # 假設3%無風險利率
            return 0.0

        except Exception:
            return 0.0

    def _create_validation_result(self,
                                 test_name: str,
                                 test_statistic: float,
                                 df: int,
                                 critical_value: Optional[float] = None) -> ValidationResult:
        """創建驗證結果"""
        p_value = 2 * (1 - stats.t.cdf(abs(test_statistic), df)) if critical_value is None else None

        return ValidationResult(
            test_name=test_name,
            test_type='statistical',
            statistic_value=test_statistic,
            p_value=p_value or 0.0,
            critical_value=critical_value or 0.0,
            is_significant=p_value is not None and p_value < self.significance_level,
            confidence_level=self.confidence_level,
            interpretation=f"Statistical test: {test_name}"
        )

    def generate_comprehensive_report(self,
                                     validation_results: List[ValidationResult],
                                     stability_analysis: Dict[str, ParameterStabilityResult],
                                     out_of_sample_results: List[OutOfSampleValidationResult]) -> StatisticalReport:
        """
        生成綜合統計驗證報告

        Args:
            validation_results: 驗證結果列表
            stability_analysis: 穩定性分析結果
            out_of_sample_results: 樣本外驗證結果

        Returns:
            統計報告
        """
        logger.info("Generating comprehensive statistical validation report")

        # 計算風險指標
        risk_metrics = self._calculate_risk_metrics(validation_results, out_of_sample_results)

        # 生成建議
        recommendations = self._generate_recommendations(
            validation_results, stability_analysis, out_of_sample_results, risk_metrics
        )

        # 總體評估
        overall_assessment = self._generate_overall_assessment(
            validation_results, stability_analysis, out_of_sample_results, risk_metrics
        )

        report = StatisticalReport(
            validator_id=f"validator_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=time.time(),
            validation_results=validation_results,
            stability_analysis=stability_analysis,
            out_of_sample_results=out_of_sample_results,
            risk_metrics=risk_metrics,
            recommendations=recommendations,
            overall_assessment=overall_assessment
        )

        # 記錄驗證歷史
        self.validation_history.append(report)

        logger.info(f"Comprehensive report generated with "
                   f"{len(validation_results)} validations, "
                   f"{len(stability_analysis)} stability analyses, "
                   f"{len(out_of_sample_results)} out-of-sample tests")

        return report

    def _calculate_risk_metrics(self,
                                 validation_results: List[ValidationResult],
                                 out_of_sample_results: List[OutOfSampleValidationResult]) -> Dict[str, float]:
        """計算風險指標"""
        metrics = {}

        # 統計顯著性檢驗通過率
        significant_tests = sum(1 for r in validation_results if r.is_significant)
        total_tests = len(validation_results)
        metrics['significance_test_pass_rate'] = significant_tests / total_tests if total_tests > 0 else 0

        # 計算過度擬合風險
        if out_of_sample_results:
            # 簡化處理，使用validation_score作為過度擬合指標
            avg_validation = np.mean([r.validation_score for r in out_of_sample_results])
            max_validation = max([r.validation_score for r in out_of_sample_results])
            metrics['average_overfitting_risk'] = avg_validation
            metrics['max_overfitting_risk'] = max_validation
        else:
            metrics['average_overfitting_risk'] = 0.0
            metrics['max_overfitting_risk'] = 0.0

        # 計算驗證可靠性
        if self.validation_history:
            recent_validations = self.validation_history[-5:]
            avg_significance = np.mean([len(r.validation_results) for r in recent_validations])
            metrics['validation_reliability'] = min(1.0, avg_significance / 10)  # 簡化計算

        return metrics

    def _generate_recommendations(self,
                                 validation_results: List[ValidationResult],
                                 stability_analysis: Dict[str, ParameterStabilityResult],
                                 out_of_sample_results: List[OutOfSampleValidationResult],
                                 risk_metrics: Dict[str, float]) -> List[str]:
        """生成建議"""
        recommendations = []

        # 基於驗證結果的建議
        significant_tests = sum(1 for r in validation_results if r.is_significant)
        if significant_tests < len(validation_results) * 0.5:
            recommendations.append("Consider collecting more data or refining strategy parameters")

        # 基於穩定性分析的建議
        unstable_parameters = [name for name, result in stability_analysis.items()
                              if result.stability_score < 0.5]
        if unstable_parameters:
            recommendations.append(f"Review and re-optimize parameters: {', '.join(unstable_parameters)}")

        # 基於樣本外驗證的建議
        if out_of_sample_results:
            high_overfitting = [r for r in out_of_sample_results if r.overfitting_score > 0.7]
            if high_overfitting:
                recommendations.append("Implement regularization techniques or simpler model architecture")

        # 基於風險指標的建議
        if risk_metrics.get('max_overfitting_risk', 0) > 0.8:
            recommendations.append("High overfitting risk detected - consider model simplification")

        return recommendations

    def _generate_overall_assessment(self,
                                    validation_results: List[ValidationResult],
                                    stability_analysis: Dict[str, ParameterStabilityResult],
                                    out_of_sample_results: List[OutOfSampleValidationResult],
                                    risk_metrics: Dict[str, float]) -> str:
        """生成總體評估"""
        assessments = []

        # 統計整體分數
        if validation_results:
            pass_rate = sum(1 for r in validation_results if r.is_significant) / len(validation_results)
            if pass_rate > 0.8:
                assessments.append("Statistical validation results are strong")
            elif pass_rate > 0.6:
                assessments.append("Statistical validation results are moderate")
            else:
                assessments.append("Statistical validation results are weak")

        # 評估穩定性
        if stability_analysis:
            avg_stability = np.mean([r.stability_score for r in stability_analysis.values()])
            if avg_stability > 0.8:
                assessments.append("Parameter stability is excellent")
            elif avg_stability > 0.6:
                assessments.append("Parameter stability is good")
            else:
                assessments.append("Parameter stability needs improvement")

        # 評估樣本外性能
        if out_of_sample_results:
            valid_tests = sum(1 for r in out_of_sample_results if r.is_valid)
            if valid_tests == len(out_of_sample_results):
                assessments.append("Out-of-sample performance is excellent")
            elif valid_tests > len(out_of_samples_results) * 0.7:
                assessments.append("Out-of-sample performance is good")
            else:
                assessments.append("Out-of-sample performance needs improvement")

        return "; ".join(assessments) if assessments else "Assessment requires more data"

    def export_validation_report(self,
                                    report: StatisticalReport,
                                    filepath: str,
                                    format: str = 'json') -> None:
        """導出驗證報告"""
        try:
            report_data = {
                'validator_id': report.validator_id,
                'timestamp': report.timestamp,
                'validation_results': [
                    {
                        'test_name': r.test_name,
                        'test_type': r.test_type,
                        'statistic_value': r.statistic_value,
                        'p_value': r.p_value,
                        'critical_value': r.critical_value,
                        'is_significant': r.is_significant,
                        'confidence_level': r.confidence_level,
                        'effect_size': r.effect_size,
                        'interpretation': r.interpretation,
                        'timestamp': r.timestamp
                    }
                    for r in report.validation_results
                ],
                'stability_analysis': {
                    name: {
                        'parameter_name': result.parameter_name,
                        'parameter_value': result.parameter_value,
                        'stability_score': result.stability_score,
                        'variance_coefficient': result.variance_coefficient,
                        'temporal_consistency': result.temporal_consistency,
                        'sensitivity_score': result.sensitivity_score,
                        'robust_range': result.robust_range,
                        'recommendation': result.recommendation
                    }
                    for name, result in report.stability_analysis.items()
                },
                'out_of_sample_results': [
                    {
                        'in_sample_sharpe': r.in_sample_sharpe,
                        'out_of_sample_sharpe': r.out_of_sample_sharpe,
                        'performance_degradation': r.performance_degradation,
                        'degradation_percentage': r.degradation_percentage,
                        'is_valid': r.is_valid,
                        'overfitting_score': r.overfitting_score,
                        'validation_periods': r.validation_periods,
                        'interpretation': r.interpretation
                    }
                    for r in report.out_of_sample_results
                ],
                'risk_metrics': report.risk_metrics,
                'recommendations': report.recommendations,
                'overall_assessment': report.overall_assessment
            }

            if format.lower() == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
            else:
                # 可以添加其他格式支持
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Validation report exported to: {filepath}")

        except Exception as e:
            logger.error(f"Error exporting validation report: {e}")

# 便利函數
def create_statistical_validator(confidence_level: float = 0.95) -> AdvancedStatisticalValidator:
    """
    創建高級統計驗證器實例

    Args:
        confidence_level: 置信水平

    Returns:
        高級統計驗證器實例
    """
    return AdvancedStatisticalValidator(confidence_level=confidence_level)

if __name__ == "__main__":
    # 測試高級統計驗證器
    logging.basicConfig(level=logging.INFO)

    # 創建驗證器
    validator = create_statistical_validator()

    # 模擬數據
    np.random.seed(42)
    n_samples = 252

    # 生成回報數據
    dates = pd.date_range('2023-01-01', periods=n_samples, freq='D')
    benchmark_returns = np.random.normal(0.0001, 0.02, n_samples)
    strategy_returns = np.random.normal(0.0002, 0.025, n_samples)  # 略好的策略

    # 添加一些相關性
    strategy_returns += 0.5 * benchmark_returns + np.random.normal(0, 0.01, n_samples)

    benchmark_series = pd.Series(benchmark_returns, index=dates)
    strategy_series = pd.Series(strategy_returns, index=dates)

    # 執行各種驗證
    print("=== Statistical Validation Test ===")

    # 1. 統計顯著性檢驗
    t_test_result = validator.perform_statistical_significance_test(
        benchmark_series, strategy_series, 'paired_t'
    )
    print(f"Paired t-test: {t_test_result.is_significant} (p={t_test_result.p_value:.4f})")

    # 2. 參數穩定性分析
    parameter_history = [
        {'rsi_period': 14, 'oversold': 30},
        {'rsi_period': 15, 'oversold': 28},
        {'rsi_period': 14, 'oversold': 32},
        {'rsi_period': 13, 'oversold': 30}
    ]
    performance_history = [1.2, 1.5, 1.3, 1.4]

    stability_results = validator.analyze_parameter_stability(
        parameter_history, performance_history
    )
    for param, result in stability_results.items():
        print(f"{param}: Stability={result.stability_score:.3f}, "
              f"VC={result.variance_coefficient:.3f}")

    # 3. 樣本外驗證
    train_data = strategy_series[:-60]
    test_data = strategy_series[-60:]

    oos_result = validator.validate_out_of_sample_performance(
        train_data, test_data, "test_strategy"
    )
    print(f"Out-of-sample validation: {oos_result.is_valid} "
          f"(Degradation: {oos_result.degradation_percentage:.1f}%)")

    # 4. 生成綜合報告
    comprehensive_report = validator.generate_comprehensive_report(
        [t_test_result],
        stability_results,
        [os_result]
    )

    print("\n=== Comprehensive Statistical Report ===")
    print(f"Validator ID: {comprehensive_report.validator_id}")
    print(f"Overall Assessment: {comprehensive_report.overall_assessment}")
    print(f"Recommendations: {len(comprehensive_report.recommendations)}")

    # 導出報告
    report_path = "statistical_validation_report.json"
    validator.export_validation_report(comprehensive_report, report_path)
    print(f"Report exported to: {report_path}")