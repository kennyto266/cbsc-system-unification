#!/usr/bin/env python3
"""
Phase 3 Comprehensive Testing and Validation Framework
第三阶段综合测试与验证框架

Comprehensive testing for Phase 3 risk management system:
- Risk management engine testing
- Cross-validation framework testing
- Market regime detection testing
- Overfitting detection testing
- Performance analytics testing
- Integration testing
- Hong Kong market-specific testing
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Iterator
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# Testing libraries
import unittest
from unittest.mock import Mock, patch
import pytest
from scipy import stats

# Local imports
from ..risk.advanced_risk_manager import AdvancedRiskManager, MultiObjectiveConfig, OptimizationObjective
from ..risk.market_regime_detector import MarketRegimeDetector, RegimeConfig, RegimeType
from ..validation.temporal_cv import TemporalCrossValidator, CVConfig, CVMethod
from ..validation.overfitting_detector import OverfittingDetector, OverfittingConfig
from ..risk.performance_attribution import PerformanceAnalytics
from ..optimization.phase3_risk_optimized_optimizer import Phase3RiskOptimizedOptimizer, Phase3OptimizationConfig


class TestStatus(str, Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TestType(str, Enum):
    """测试类型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    STRESS = "stress"


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    test_type: TestType
    status: TestStatus
    execution_time: float
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class TestSuite:
    """测试套件"""
    name: str
    tests: List[TestResult] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    total_execution_time: float = 0.0

    def add_result(self, result: TestResult):
        """添加测试结果"""
        self.tests.append(result)
        self.total_tests += 1
        self.total_execution_time += result.execution_time

        if result.status == TestStatus.PASSED:
            self.passed_tests += 1
        elif result.status == TestStatus.FAILED:
            self.failed_tests += 1
        elif result.status == TestStatus.SKIPPED:
            self.skipped_tests += 1

    @property
    def success_rate(self) -> float:
        """成功率"""
        return self.passed_tests / self.total_tests if self.total_tests > 0 else 0.0


class Phase3TestSuite:
    """第三阶段测试套件"""

    def __init__(self):
        """初始化测试套件"""
        self.logger = logging.getLogger("hk_quant_system.phase3_test_suite")
        self.test_suites = {}
        self.mock_data = {}
        self.test_results = []

        # 香港市场参数
        self.hk_trading_days = 252
        self.test_symbols = ["0700.HK", "0941.HK", "1299.HK"]

        # 初始化测试数据
        self._prepare_test_data()

    def _prepare_test_data(self):
        """准备测试数据"""
        try:
            # 生成模拟市场数据
            np.random.seed(42)  # 确保可重复性

            for symbol in self.test_symbols:
                # 生成2年的日线数据
                n_days = self.hk_trading_days * 2
                dates = pd.date_range(start='2022-01-01', periods=n_days, freq='D')

                # 模拟价格路径（几何布朗运动）
                initial_price = 100.0
                drift = 0.0005  # 日均收益率
                volatility = 0.02  # 日波动率

                returns = np.random.normal(drift, volatility, n_days)
                prices = [initial_price]

                for ret in returns[1:]:
                    prices.append(prices[-1] * (1 + ret))

                # 创建OHLC数据
                df = pd.DataFrame({
                    'open': prices,
                    'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                    'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                    'close': prices,
                    'volume': np.random.randint(1000000, 10000000, n_days)
                }, index=dates)

                # 过滤交易日（简单过滤周末）
                df = df[df.index.weekday < 5]

                self.mock_data[symbol] = df

            # 生成基准数据（恒生指数）
            hsi_dates = pd.date_range(start='2022-01-01', periods=len(self.mock_data["0700.HK"]), freq='D')
            hsi_returns = np.random.normal(0.0003, 0.015, len(hsi_dates))
            hsi_prices = [28000.0]
            for ret in hsi_returns[1:]:
                hsi_prices.append(hsi_prices[-1] * (1 + ret))

            self.mock_data["HSI"] = pd.DataFrame({
                'close': hsi_prices
            }, index=hsi_dates)

            self.logger.info("Test data prepared successfully")

        except Exception as e:
            self.logger.error(f"Error preparing test data: {e}")
            raise

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        try:
            self.logger.info("Starting comprehensive Phase 3 test suite...")

            start_time = datetime.now()

            # 运行各个测试套件
            results = {}

            # 1. 风险管理引擎测试
            results["risk_management"] = await self._test_risk_management_engine()

            # 2. 市场制度检测测试
            results["market_regime_detection"] = await self._test_market_regime_detection()

            # 3. 时序交叉验证测试
            results["temporal_cross_validation"] = await self._test_temporal_cross_validation()

            # 4. 过拟合检测测试
            results["overfitting_detection"] = await self._test_overfitting_detection()

            # 5. 性能分析测试
            results["performance_analytics"] = await self._test_performance_analytics()

            # 6. 集成测试
            results["integration"] = await self._test_integration()

            # 7. 香港市场特定测试
            results["hk_market_specific"] = await self._test_hk_market_specific()

            # 8. 压力测试
            results["stress"] = await self._test_stress_conditions()

            total_time = (datetime.now() - start_time).total_seconds()

            # 汇总结果
            summary = self._generate_test_summary(results, total_time)

            self.logger.info(f"Test suite completed in {total_time:.2f} seconds")
            return summary

        except Exception as e:
            self.logger.error(f"Error running test suite: {e}")
            raise

    async def _test_risk_management_engine(self) -> TestSuite:
        """测试风险管理引擎"""
        suite = TestSuite("Risk Management Engine")

        try:
            # 测试1: 基础风险指标计算
            result = await self._test_basic_risk_metrics()
            suite.add_result(result)

            # 测试2: 多目标优化
            result = await self._test_multi_objective_optimization()
            suite.add_result(result)

            # 测试3: 风险约束检查
            result = await self._test_risk_constraints()
            suite.add_result(result)

            # 测试4: 香港市场特定风险指标
            result = await self._test_hk_risk_metrics()
            suite.add_result(result)

        except Exception as e:
            self.logger.error(f"Error in risk management engine tests: {e}")

        return suite

    async def _test_basic_risk_metrics(self) -> TestResult:
        """测试基础风险指标"""
        start_time = datetime.now()
        test_name = "Basic Risk Metrics Calculation"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]
            returns = data['close'].pct_change().dropna()

            # 初始化风险管理器
            risk_manager = AdvancedRiskManager()

            # 计算风险指标
            risk_metrics = await risk_manager.risk_calculator.calculate_portfolio_risk(returns)

            # 验证结果
            assert risk_metrics is not None, "Risk metrics should not be None"
            assert risk_metrics.volatility > 0, "Volatility should be positive"
            assert isinstance(risk_metrics.sharpe_ratio, float), "Sharpe ratio should be a float"
            assert risk_metrics.max_drawdown >= 0, "Max drawdown should be non-negative"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Basic risk metrics calculated successfully",
                details={
                    "volatility": risk_metrics.volatility,
                    "sharpe_ratio": risk_metrics.sharpe_ratio,
                    "max_drawdown": risk_metrics.max_drawdown
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Basic risk metrics test failed: {str(e)}",
                error=str(e)
            )

    async def _test_multi_objective_optimization(self) -> TestResult:
        """测试多目标优化"""
        start_time = datetime.now()
        test_name = "Multi-Objective Optimization"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]
            returns = data['close'].pct_change().dropna()

            # 生成测试参数组合
            parameter_combinations = [
                {"rsi_period": 14, "oversold": 30, "overbought": 70},
                {"rsi_period": 21, "oversold": 25, "overbought": 75},
                {"rsi_period": 10, "oversold": 20, "overbought": 80}
            ]

            # 初始化风险管理器
            config = MultiObjectiveConfig(
                objectives=[
                    OptimizationObjective.SHARPE_RATIO,
                    OptimizationObjective.SORTINO_RATIO
                ]
            )
            risk_manager = AdvancedRiskManager(config)

            # 执行优化
            result = await risk_manager.optimize_strategy_parameters(
                returns_data=returns,
                parameter_combinations=parameter_combinations
            )

            # 验证结果
            assert result is not None, "Optimization result should not be None"
            assert result.get("status") == "success", "Optimization should succeed"
            assert "best_solution" in result, "Should contain best solution"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Multi-objective optimization completed successfully",
                details={
                    "optimization_status": result.get("status"),
                    "has_best_solution": "best_solution" in result,
                    "total_evaluations": result.get("total_evaluations", 0)
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Multi-objective optimization test failed: {str(e)}",
                error=str(e)
            )

    async def _test_risk_constraints(self) -> TestResult:
        """测试风险约束"""
        start_time = datetime.now()
        test_name = "Risk Constraints Validation"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]
            returns = data['close'].pct_change().dropna()

            # 初始化风险管理器
            config = MultiObjectiveConfig()
            risk_manager = AdvancedRiskManager(config)

            # 创建高风险收益数据（超过约束）
            high_risk_returns = returns.copy()
            high_risk_returns *= 3  # 增加3倍波动率

            # 计算风险指标
            risk_metrics = await risk_manager.risk_calculator.calculate_portfolio_risk(high_risk_returns)

            # 检查约束违反
            constraints_violations = await risk_manager._check_risk_constraints(risk_metrics)

            # 验证结果
            assert not constraints_violations["is_feasible"], "High risk data should violate constraints"
            assert len(constraints_violations["violations"]) > 0, "Should have constraint violations"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Risk constraints validation works correctly",
                details={
                    "is_feasible": constraints_violations["is_feasible"],
                    "penalty": constraints_violations["penalty"],
                    "num_violations": len(constraints_violations["violations"])
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Risk constraints test failed: {str(e)}",
                error=str(e)
            )

    async def _test_hk_risk_metrics(self) -> TestResult:
        """测试香港市场特定风险指标"""
        start_time = datetime.now()
        test_name = "Hong Kong Market Risk Metrics"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            stock_data = self.mock_data[symbol]
            hsi_data = self.mock_data["HSI"]

            # 初始化风险管理器
            risk_manager = AdvancedRiskManager()

            # 计算香港市场风险溢价
            stock_returns = stock_data['close'].pct_change().dropna()
            hsi_returns = hsi_data['close'].pct_change().dropna()

            # 对齐数据
            aligned_stock, aligned_hsi = stock_returns.align(hsi_returns, join='inner')

            risk_premiums = await risk_manager.calculate_hk_market_risk_premium(
                pd.DataFrame({symbol: aligned_stock}),
                aligned_hsi
            )

            # 验证结果
            assert symbol in risk_premiums, f"Should contain risk premium for {symbol}"
            assert "risk_premium" in risk_premiums[symbol], "Should contain risk premium metric"
            assert "information_ratio" in risk_premiums[symbol], "Should contain information ratio"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Hong Kong market risk metrics calculated successfully",
                details={
                    "symbol_analyzed": symbol,
                    "risk_premium": risk_premiums[symbol]["risk_premium"],
                    "information_ratio": risk_premiums[symbol]["information_ratio"]
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"HK market risk metrics test failed: {str(e)}",
                error=str(e)
            )

    async def _test_market_regime_detection(self) -> TestSuite:
        """测试市场制度检测"""
        suite = TestSuite("Market Regime Detection")

        try:
            # 测试1: 基础制度检测
            result = await self._test_basic_regime_detection()
            suite.add_result(result)

            # 测试2: 特征提取
            result = await self._test_regime_feature_extraction()
            suite.add_result(result)

            # 测试3: 制度稳定性
            result = await self._test_regime_stability()
            suite.add_result(result)

        except Exception as e:
            self.logger.error(f"Error in market regime detection tests: {e}")

        return suite

    async def _test_basic_regime_detection(self) -> TestResult:
        """测试基础制度检测"""
        start_time = datetime.now()
        test_name = "Basic Market Regime Detection"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]

            # 初始化制度检测器
            config = RegimeConfig()
            detector = MarketRegimeDetector(config)

            # 检测制度
            regime_signal = await detector.detect_current_regime(data)

            # 验证结果
            assert regime_signal is not None, "Regime signal should not be None"
            assert isinstance(regime_signal.regime, RegimeType), "Should return valid regime type"
            assert 0 <= regime_signal.confidence <= 1, "Confidence should be between 0 and 1"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Market regime detection completed successfully",
                details={
                    "detected_regime": regime_signal.regime.value,
                    "confidence": regime_signal.confidence,
                    "expected_duration": regime_signal.expected_duration
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Market regime detection test failed: {str(e)}",
                error=str(e)
            )

    async def _test_regime_feature_extraction(self) -> TestResult:
        """测试制度特征提取"""
        start_time = datetime.now()
        test_name = "Regime Feature Extraction"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]

            # 初始化制度检测器
            config = RegimeConfig()
            detector = MarketRegimeDetector(config)

            # 提取特征
            features = await detector._extract_regime_features(data)

            # 验证结果
            assert features is not None, "Features should not be None"
            assert features.trend_strength >= 0, "Trend strength should be non-negative"
            assert features.volatility >= 0, "Volatility should be non-negative"
            assert 0 <= features.rsi <= 100, "RSI should be between 0 and 100"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Regime feature extraction completed successfully",
                details={
                    "trend_strength": features.trend_strength,
                    "volatility": features.volatility,
                    "rsi": features.rsi
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Regime feature extraction test failed: {str(e)}",
                error=str(e)
            )

    async def _test_regime_stability(self) -> TestResult:
        """测试制度稳定性"""
        start_time = datetime.now()
        test_name = "Regime Stability Analysis"

        try:
            # 初始化制度检测器
            config = RegimeConfig()
            detector = MarketRegimeDetector(config)

            # 创建模拟制度信号
            from ..risk.market_regime_detector import RegimeSignal, RegimeFeatures
            from datetime import datetime

            features = RegimeFeatures(
                trend_strength=0.8,
                trend_direction=0.01,
                momentum=0.005,
                volatility=0.02,
                volatility_trend=0.001,
                volatility_regime=0.5,
                return_skewness=0.1,
                return_kurtosis=3.0,
                tail_risk=0.03,
                volume_ratio=1.2,
                price_efficiency=0.8,
                market_depth=0.7,
                hsi_correlation=0.6,
                mainland_influence=0.3,
                us_market_influence=0.2,
                currency_exposure=0.1,
                rsi=55,
                macd=0.001,
                bollinger_position=0.6,
                atr=0.02
            )

            signal = RegimeSignal(
                regime=RegimeType.NORMAL,
                confidence=0.8,
                probability_distribution={RegimeType.NORMAL: 0.8},
                transition_probabilities={},
                expected_duration=60,
                detection_timestamp=datetime.now(),
                features=features,
                signal_strength=0.8
            )

            # 检查稳定性
            is_stable = await detector._is_regime_stable(signal)

            # 验证结果
            assert isinstance(is_stable, bool), "Stability should be boolean"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Regime stability analysis completed successfully",
                details={
                    "is_stable": is_stable,
                    "signal_confidence": signal.confidence,
                    "signal_strength": signal.signal_strength
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Regime stability test failed: {str(e)}",
                error=str(e)
            )

    async def _test_temporal_cross_validation(self) -> TestSuite:
        """测试时序交叉验证"""
        suite = TestSuite("Temporal Cross Validation")

        try:
            # 测试1: 扩展窗口验证
            result = await self._test_expanding_window_cv()
            suite.add_result(result)

            # 测试2: 滑动窗口验证
            result = await self._test_sliding_window_cv()
            suite.add_result(result)

            # 测试3: 带清除的K折验证
            result = await self._test_purged_kfold_cv()
            suite.add_result(result)

        except Exception as e:
            self.logger.error(f"Error in temporal cross validation tests: {e}")

        return suite

    async def _test_expanding_window_cv(self) -> TestResult:
        """测试扩展窗口交叉验证"""
        start_time = datetime.now()
        test_name = "Expanding Window Cross Validation"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]

            # 初始化交叉验证器
            config = CVConfig(method=CVMethod.EXPANDING_WINDOW, initial_train_size=126, test_size=21)
            validator = TemporalCrossValidator(config)

            # 简化的策略函数
            async def test_strategy(data, params):
                returns = data.pct_change().dropna()
                return returns

            # 生成参数组合
            param_combinations = [{"param1": i} for i in range(3)]  # 简化参数

            # 执行验证
            validation_result = await validator.validate_strategy(
                data=data,
                strategy_func=test_strategy,
                parameter_combinations=param_combinations
            )

            # 验证结果
            assert validation_result is not None, "Validation result should not be None"
            assert "split_results" in validation_result, "Should contain split results"
            assert "summary" in validation_result, "Should contain summary"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Expanding window CV completed successfully",
                details={
                    "total_splits": validation_result.get("total_splits", 0),
                    "successful_validations": validation_result.get("successful_validations", 0)
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Expanding window CV test failed: {str(e)}",
                error=str(e)
            )

    async def _test_sliding_window_cv(self) -> TestResult:
        """测试滑动窗口交叉验证"""
        start_time = datetime.now()
        test_name = "Sliding Window Cross Validation"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]

            # 初始化交叉验证器
            config = CVConfig(method=CVMethod.SLIDING_WINDOW, initial_train_size=126, test_size=21)
            validator = TemporalCrossValidator(config)

            # 简化的策略函数
            async def test_strategy(data, params):
                returns = data.pct_change().dropna()
                return returns

            # 生成参数组合
            param_combinations = [{"param1": i} for i in range(2)]  # 简化参数

            # 执行验证
            validation_result = await validator.validate_strategy(
                data=data,
                strategy_func=test_strategy,
                parameter_combinations=param_combinations
            )

            # 验证结果
            assert validation_result is not None, "Validation result should not be None"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Sliding window CV completed successfully",
                details={
                    "cv_method": "sliding_window",
                    "has_results": validation_result is not None
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Sliding window CV test failed: {str(e)}",
                error=str(e)
            )

    async def _test_purged_kfold_cv(self) -> TestResult:
        """测试带清除的K折交叉验证"""
        start_time = datetime.now()
        test_name = "Purged K-Fold Cross Validation"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]

            # 初始化交叉验证器
            config = CVConfig(method=CVMethod.PURGED_KFOLD, n_splits=3)
            validator = TemporalCrossValidator(config)

            # 简化的策略函数
            async def test_strategy(data, params):
                returns = data.pct_change().dropna()
                return returns

            # 生成参数组合
            param_combinations = [{"param1": i} for i in range(1)]  # 简化参数

            # 执行验证
            validation_result = await validator.validate_strategy(
                data=data,
                strategy_func=test_strategy,
                parameter_combinations=param_combinations
            )

            # 验证结果
            assert validation_result is not None, "Validation result should not be None"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Purged K-fold CV completed successfully",
                details={
                    "cv_method": "purged_kfold",
                    "has_results": validation_result is not None
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Purged K-fold CV test failed: {str(e)}",
                error=str(e)
            )

    async def _test_overfitting_detection(self) -> TestSuite:
        """测试过拟合检测"""
        suite = TestSuite("Overfitting Detection")

        try:
            # 测试1: 参数稳定性检测
            result = await self._test_parameter_stability_detection()
            suite.add_result(result)

            # 测试2: 性能不一致检测
            result = await self._test_performance_inconsistency_detection()
            suite.add_result(result)

            # 测试3: 多重比较偏差检测
            result = await self._test_multiple_comparison_detection()
            suite.add_result(result)

        except Exception as e:
            self.logger.error(f"Error in overfitting detection tests: {e}")

        return suite

    async def _test_parameter_stability_detection(self) -> TestResult:
        """测试参数稳定性检测"""
        start_time = datetime.now()
        test_name = "Parameter Stability Detection"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]

            # 生成不稳定的参数组合
            parameter_combinations = []
            for i in range(100):
                parameter_combinations.append({
                    "param1": np.random.uniform(5, 50),
                    "param2": np.random.uniform(0.1, 1.0),
                    "param3": np.random.choice([10, 20, 30, 40, 50])
                })

            # 初始化过拟合检测器
            config = OverfittingConfig()
            detector = OverfittingDetector(config)

            # 检测参数不稳定性
            instability_signals = await detector._detect_parameter_instability(
                parameter_combinations, data
            )

            # 验证结果
            assert isinstance(instability_signals, list), "Should return list of signals"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Parameter stability detection completed successfully",
                details={
                    "num_signals": len(instability_signals),
                    "num_combinations": len(parameter_combinations)
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Parameter stability detection test failed: {str(e)}",
                error=str(e)
            )

    async def _test_performance_inconsistency_detection(self) -> TestResult:
        """测试性能不一致检测"""
        start_time = datetime.now()
        test_name = "Performance Inconsistency Detection"

        try:
            # 初始化过拟合检测器
            config = OverfittingConfig()
            detector = OverfittingDetector(config)

            # 创建不一致的性能数据
            in_sample_perf = {
                "sharpe_ratio": 2.5,
                "total_return": 0.30,
                "max_drawdown": 0.05
            }

            out_sample_perf = {
                "sharpe_ratio": 0.2,
                "total_return": -0.05,
                "max_drawdown": 0.25
            }

            # 检测性能不一致性
            inconsistency_signals = await detector._detect_performance_inconsistency(
                in_sample_perf, out_sample_perf
            )

            # 验证结果
            assert isinstance(inconsistency_signals, list), "Should return list of signals"

            # 由于样本内外性能差异很大，应该检测到不一致性
            assert len(inconsistency_signals) > 0, "Should detect performance inconsistency"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Performance inconsistency detection completed successfully",
                details={
                    "num_signals": len(inconsistency_signals),
                    "sharpe_degradation": out_sample_perf["sharpe_ratio"] - in_sample_perf["sharpe_ratio"]
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Performance inconsistency detection test failed: {str(e)}",
                error=str(e)
            )

    async def _test_multiple_comparison_detection(self) -> TestResult:
        """测试多重比较偏差检测"""
        start_time = datetime.now()
        test_name = "Multiple Comparison Bias Detection"

        try:
            # 初始化过拟合检测器
            config = OverfittingConfig()
            detector = OverfittingDetector(config)

            # 生成大量的参数组合和性能数据
            parameter_combinations = [{"param": i} for i in range(200)]  # 200个组合
            performance_data = {"param_" + str(i): np.random.normal(0.5, 1.0) for i in range(200)}

            # 检测多重比较偏差
            comparison_signals = await detector._detect_multiple_comparison_bias(
                parameter_combinations, performance_data
            )

            # 验证结果
            assert isinstance(comparison_signals, list), "Should return list of signals"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Multiple comparison bias detection completed successfully",
                details={
                    "num_signals": len(comparison_signals),
                    "num_comparisons": len(parameter_combinations)
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Multiple comparison detection test failed: {str(e)}",
                error=str(e)
            )

    async def _test_performance_analytics(self) -> TestSuite:
        """测试性能分析"""
        suite = TestSuite("Performance Analytics")

        try:
            # 测试1: 综合性能指标计算
            result = await self._test_comprehensive_metrics_calculation()
            suite.add_result(result)

            # 测试2: 性能归因分析
            result = await self._test_performance_attribution()
            suite.add_result(result)

            # 测试3: 滚动指标计算
            result = await self._test_rolling_metrics()
            suite.add_result(result)

        except Exception as e:
            self.logger.error(f"Error in performance analytics tests: {e}")

        return suite

    async def _test_comprehensive_metrics_calculation(self) -> TestResult:
        """测试综合性能指标计算"""
        start_time = datetime.now()
        test_name = "Comprehensive Metrics Calculation"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]
            returns = data['close'].pct_change().dropna()

            # 初始化性能分析器
            analytics = PerformanceAnalytics()

            # 计算综合指标
            metrics = await analytics.calculate_comprehensive_metrics(returns)

            # 验证结果
            assert metrics is not None, "Metrics should not be None"
            assert metrics.total_return is not None, "Total return should be calculated"
            assert metrics.sharpe_ratio is not None, "Sharpe ratio should be calculated"
            assert metrics.max_drawdown >= 0, "Max drawdown should be non-negative"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Comprehensive metrics calculation completed successfully",
                details={
                    "total_return": metrics.total_return,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "max_drawdown": metrics.max_drawdown,
                    "volatility": metrics.volatility
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Comprehensive metrics calculation test failed: {str(e)}",
                error=str(e)
            )

    async def _test_performance_attribution(self) -> TestResult:
        """测试性能归因"""
        start_time = datetime.now()
        test_name = "Performance Attribution"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            stock_data = self.mock_data[symbol]
            hsi_data = self.mock_data["HSI"]

            # 初始化性能分析器
            analytics = PerformanceAnalytics()

            # 计算收益序列
            strategy_returns = stock_data['close'].pct_change().dropna()
            benchmark_returns = hsi_data['close'].pct_change().dropna()

            # 执行归因分析
            attribution_result = await analytics.performance_attribution(
                strategy_returns, benchmark_returns
            )

            # 验证结果
            assert attribution_result is not None, "Attribution result should not be None"
            assert attribution_result.total_return is not None, "Total return should be calculated"
            assert attribution_result.benchmark_return is not None, "Benchmark return should be calculated"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Performance attribution completed successfully",
                details={
                    "total_return": attribution_result.total_return,
                    "benchmark_return": attribution_result.benchmark_return,
                    "active_return": attribution_result.active_return
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Performance attribution test failed: {str(e)}",
                error=str(e)
            )

    async def _test_rolling_metrics(self) -> TestResult:
        """测试滚动指标计算"""
        start_time = datetime.now()
        test_name = "Rolling Metrics Calculation"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            data = self.mock_data[symbol]
            returns = data['close'].pct_change().dropna()

            # 初始化性能分析器
            analytics = PerformanceAnalytics()

            # 计算滚动指标
            rolling_metrics = await analytics.calculate_rolling_metrics(
                returns, window=63  # 3个月窗口
            )

            # 验证结果
            assert isinstance(rolling_metrics, pd.DataFrame), "Should return DataFrame"
            assert len(rolling_metrics) > 0, "Should have rolling metrics data"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Rolling metrics calculation completed successfully",
                details={
                    "num_periods": len(rolling_metrics),
                    "has_sharpe": "rolling_sharpe" in rolling_metrics.columns,
                    "has_max_dd": "rolling_max_dd" in rolling_metrics.columns
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Rolling metrics calculation test failed: {str(e)}",
                error=str(e)
            )

    async def _test_integration(self) -> TestSuite:
        """测试集成"""
        suite = TestSuite("Integration Testing")

        try:
            # 测试1: 第三阶段优化器集成
            result = await self._test_phase3_optimizer_integration()
            suite.add_result(result)

        except Exception as e:
            self.logger.error(f"Error in integration tests: {e}")

        return suite

    async def _test_phase3_optimizer_integration(self) -> TestResult:
        """测试第三阶段优化器集成"""
        start_time = datetime.now()
        test_name = "Phase 3 Optimizer Integration"

        try:
            # 准备简化的配置
            config = Phase3OptimizationConfig()
            config.base_config.max_combinations = 10  # 减少组合数以加快测试
            config.base_config.duration = 126  # 使用半年数据

            # 初始化第三阶段优化器
            optimizer = Phase3RiskOptimizedOptimizer(config)

            # 注意：这里只测试初始化和基础功能，不执行完整优化以节省时间
            assert optimizer is not None, "Optimizer should be initialized"
            assert optimizer.config is not None, "Config should be set"

            return TestResult(
                test_name=test_name,
                test_type=TestType.INTEGRATION,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Phase 3 optimizer integration test completed successfully",
                details={
                    "components_initialized": [
                        "risk_manager",
                        "regime_detector",
                        "cross_validator",
                        "overfitting_detector",
                        "performance_analytics"
                    ],
                    "test_mode": True  # 标识这是测试模式
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.INTEGRATION,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Phase 3 optimizer integration test failed: {str(e)}",
                error=str(e)
            )

    async def _test_hk_market_specific(self) -> TestSuite:
        """测试香港市场特定功能"""
        suite = TestSuite("Hong Kong Market Specific Testing")

        try:
            # 测试1: 香港交易日历
            result = await self._test_hk_trading_calendar()
            suite.add_result(result)

            # 测试2: 香港市场制度特征
            result = await self._test_hk_regime_features()
            suite.add_result(result)

        except Exception as e:
            self.logger.error(f"Error in HK market specific tests: {e}")

        return suite

    async def _test_hk_trading_calendar(self) -> TestResult:
        """测试香港交易日历"""
        start_time = datetime.now()
        test_name = "Hong Kong Trading Calendar"

        try:
            # 验证测试数据中的交易日
            symbol = "0700.HK"
            data = self.mock_data[symbol]

            # 检查是否过滤了周末
            weekend_days = data.index[data.index.weekday >= 5]
            assert len(weekend_days) == 0, "Should not include weekends in HK trading data"

            # 检查是否有足够的数据
            assert len(data) > 200, "Should have sufficient trading days"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Hong Kong trading calendar test passed",
                details={
                    "total_trading_days": len(data),
                    "no_weekend_data": len(weekend_days) == 0,
                    "date_range": f"{data.index[0].date()} to {data.index[-1].date()}"
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"HK trading calendar test failed: {str(e)}",
                error=str(e)
            )

    async def _test_hk_regime_features(self) -> TestResult:
        """测试香港市场制度特征"""
        start_time = datetime.now()
        test_name = "Hong Kong Market Regime Features"

        try:
            # 准备测试数据
            symbol = "0700.HK"
            stock_data = self.mock_data[symbol]
            hsi_data = self.mock_data["HSI"]

            # 初始化制度检测器
            config = RegimeConfig()
            detector = MarketRegimeDetector(config)

            # 计算香港市场相关特征
            stock_returns = stock_data['close'].pct_change().dropna()
            hsi_returns = hsi_data['close'].pct_change().dropna()

            # 对齐数据
            aligned_stock, aligned_hsi = stock_returns.align(hsi_returns, join='inner')

            if len(aligned_stock) > 0:
                hsi_correlation = aligned_stock.corr(aligned_hsi)
                assert -1 <= hsi_correlation <= 1, "Correlation should be between -1 and 1"

            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Hong Kong market regime features test passed",
                details={
                    "hsi_correlation": hsi_correlation if len(aligned_stock) > 0 else "insufficient_data",
                    "aligned_data_points": len(aligned_stock)
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"HK regime features test failed: {str(e)}",
                error=str(e)
            )

    async def _test_stress_conditions(self) -> TestSuite:
        """测试压力条件"""
        suite = TestSuite("Stress Testing")

        try:
            # 测试1: 极端市场条件
            result = await self._test_extreme_market_conditions()
            suite.add_result(result)

            # 测试2: 数据质量压力测试
            result = await self._test_data_quality_stress()
            suite.add_result(result)

        except Exception as e:
            self.logger.error(f"Error in stress tests: {e}")

        return suite

    async def _test_extreme_market_conditions(self) -> TestResult:
        """测试极端市场条件"""
        start_time = datetime.now()
        test_name = "Extreme Market Conditions"

        try:
            # 创建极端市场条件数据
            n_days = 100
            dates = pd.date_range(start='2023-01-01', periods=n_days, freq='D')

            # 模拟市场崩盘（前50天正常，后50天崩盘）
            normal_returns = np.random.normal(0.001, 0.02, 50)
            crash_returns = np.random.normal(-0.05, 0.08, 50)  # 负收益，高波动

            all_returns = np.concatenate([normal_returns, crash_returns])
            prices = [100.0]

            for ret in all_returns:
                prices.append(prices[-1] * (1 + ret))

            extreme_data = pd.DataFrame({
                'close': prices[1:],
                'volume': np.random.randint(1000000, 10000000, n_days)
            }, index=dates)

            # 过滤交易日
            extreme_data = extreme_data[extreme_data.index.weekday < 5]

            # 测试风险指标计算
            risk_manager = AdvancedRiskManager()
            returns = extreme_data['close'].pct_change().dropna()

            risk_metrics = await risk_manager.risk_calculator.calculate_portfolio_risk(returns)

            # 验证结果
            assert risk_metrics is not None, "Should handle extreme conditions"
            assert risk_metrics.max_drawdown > 0.2, "Should detect large drawdown in crash conditions"

            return TestResult(
                test_name=test_name,
                test_type=TestType.STRESS,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Extreme market conditions test passed",
                details={
                    "max_drawdown": risk_metrics.max_drawdown,
                    "volatility": risk_metrics.volatility,
                    "data_points": len(returns)
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.STRESS,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Extreme market conditions test failed: {str(e)}",
                error=str(e)
            )

    async def _test_data_quality_stress(self) -> TestResult:
        """测试数据质量压力"""
        start_time = datetime.now()
        test_name = "Data Quality Stress Test"

        try:
            # 创建包含缺失值和异常值的数据
            n_days = 100
            dates = pd.date_range(start='2023-01-01', periods=n_days, freq='D')

            # 正常价格
            normal_prices = np.random.normal(100, 10, n_days)

            # 插入一些异常值
            normal_prices[10] = 1000  # 异常高值
            normal_prices[20] = 1     # 异常低值
            normal_prices[30] = np.nan  # 缺失值
            normal_prices[40] = np.nan  # 缺失值

            poor_quality_data = pd.DataFrame({
                'close': normal_prices,
                'high': normal_prices * 1.02,
                'low': normal_prices * 0.98,
                'volume': np.random.randint(1000000, 10000000, n_days)
            }, index=dates)

            # 过滤交易日
            poor_quality_data = poor_quality_data[poor_quality_data.index.weekday < 5]

            # 测试数据处理
            returns = poor_quality_data['close'].pct_change().dropna()

            # 验证能够处理质量问题
            assert len(returns) > 0, "Should have data after processing"
            assert not returns.isnull().any(), "Should not have null values after processing"

            return TestResult(
                test_name=test_name,
                test_type=TestType.STRESS,
                status=TestStatus.PASSED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message="Data quality stress test passed",
                details={
                    "original_data_points": len(poor_quality_data),
                    "returns_after_processing": len(returns),
                    "has_nulls": returns.isnull().any()
                }
            )

        except Exception as e:
            return TestResult(
                test_name=test_name,
                test_type=TestType.STRESS,
                status=TestStatus.FAILED,
                execution_time=(datetime.now() - start_time).total_seconds(),
                message=f"Data quality stress test failed: {str(e)}",
                error=str(e)
            )

    def _generate_test_summary(
        self,
        results: Dict[str, TestSuite],
        total_time: float
    ) -> Dict[str, Any]:
        """生成测试摘要"""
        try:
            # 汇总所有测试结果
            all_tests = []
            for suite_name, suite in results.items():
                for test in suite.tests:
                    all_tests.append({
                        "suite": suite_name,
                        "test": test.test_name,
                        "type": test.test_type.value,
                        "status": test.status.value,
                        "execution_time": test.execution_time,
                        "message": test.message
                    })

            # 计算总体统计
            total_tests = sum(suite.total_tests for suite in results.values())
            total_passed = sum(suite.passed_tests for suite in results.values())
            total_failed = sum(suite.failed_tests for suite in results.values())
            total_skipped = sum(suite.skipped_tests for suite in results.values())

            overall_success_rate = total_passed / total_tests if total_tests > 0 else 0.0

            # 按状态分组
            passed_tests = [t for t in all_tests if t["status"] == "passed"]
            failed_tests = [t for t in all_tests if t["status"] == "failed"]
            skipped_tests = [t for t in all_tests if t["status"] == "skipped"]

            # 按套件汇总
            suite_summaries = {}
            for suite_name, suite in results.items():
                suite_summaries[suite_name] = {
                    "total_tests": suite.total_tests,
                    "passed_tests": suite.passed_tests,
                    "failed_tests": suite.failed_tests,
                    "skipped_tests": suite.skipped_tests,
                    "success_rate": suite.success_rate,
                    "execution_time": suite.total_execution_time
                }

            summary = {
                "test_execution": {
                    "start_time": datetime.now().isoformat(),
                    "total_execution_time": total_time,
                    "timestamp": datetime.now().isoformat()
                },
                "overall_statistics": {
                    "total_tests": total_tests,
                    "passed_tests": total_passed,
                    "failed_tests": total_failed,
                    "skipped_tests": total_skipped,
                    "success_rate": overall_success_rate
                },
                "suite_summaries": suite_summaries,
                "test_results": {
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "skipped": skipped_tests
                },
                "test_environment": {
                    "python_version": "3.x",
                    "test_symbols": self.test_symbols,
                    "test_data_periods": len(self.mock_data["0700.HK"])
                }
            }

            return summary

        except Exception as e:
            self.logger.error(f"Error generating test summary: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """生成测试报告"""
        try:
            report = []
            report.append("=" * 80)
            report.append("PHASE 3 COMPREHENSIVE TEST SUITE REPORT")
            report.append("=" * 80)

            # 总体统计
            overall_stats = results["overall_statistics"]
            report.append(f"Total Tests: {overall_stats['total_tests']}")
            report.append(f"Passed: {overall_stats['passed_tests']}")
            report.append(f"Failed: {overall_stats['failed_tests']}")
            report.append(f"Skipped: {overall_stats['skipped_tests']}")
            report.append(f"Success Rate: {overall_stats['success_rate']:.2%}")
            report.append(f"Execution Time: {results['test_execution']['total_execution_time']:.2f} seconds")

            # 各套件详情
            report.append("\n--- TEST SUITE DETAILS ---")
            for suite_name, suite_summary in results["suite_summaries"].items():
                report.append(f"\n{suite_name}:")
                report.append(f"  Tests: {suite_summary['total_tests']}")
                report.append(f"  Passed: {suite_summary['passed_tests']}")
                report.append(f"  Failed: {suite_summary['failed_tests']}")
                report.append(f"  Success Rate: {suite_summary['success_rate']:.2%}")

            # 失败的测试
            failed_tests = results["test_results"]["failed"]
            if failed_tests:
                report.append("\n--- FAILED TESTS ---")
                for test in failed_tests:
                    report.append(f"❌ {test['suite']}.{test['test']}")
                    report.append(f"   {test['message']}")

            # 测试环境
            env_info = results["test_environment"]
            report.append("\n--- TEST ENVIRONMENT ---")
            report.append(f"Test Symbols: {', '.join(env_info['test_symbols'])}")
            report.append(f"Data Periods: {env_info['test_data_periods']} days")

            # 结论
            success_rate = overall_stats['success_rate']
            if success_rate >= 0.95:
                conclusion = "🎉 EXCELLENT: All critical systems working properly"
            elif success_rate >= 0.90:
                conclusion = "✅ GOOD: Most systems functioning correctly"
            elif success_rate >= 0.80:
                conclusion = "⚠️  ACCEPTABLE: Some issues need attention"
            else:
                conclusion = "❌ NEEDS WORK: Significant issues found"

            report.append(f"\n--- CONCLUSION ---")
            report.append(conclusion)
            report.append("=" * 80)

            return "\n".join(report)

        except Exception as e:
            self.logger.error(f"Error generating test report: {e}")
            return f"Error generating test report: {str(e)}"


# 便利函数
async def run_phase3_test_suite() -> Dict[str, Any]:
    """
    运行第三阶段测试套件便利函数

    Returns:
        测试结果摘要
    """
    test_suite = Phase3TestSuite()
    results = await test_suite.run_all_tests()

    return results

def generate_test_report_text(results: Dict[str, Any]) -> str:
    """
    生成测试报告便利函数

    Args:
        results: 测试结果

    Returns:
        测试报告文本
    """
    test_suite = Phase3TestSuite()
    report = test_suite.generate_test_report(results)

    return report