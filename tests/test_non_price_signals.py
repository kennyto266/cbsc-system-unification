#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非价格信号系统综合测试套件 - Comprehensive Non-Price Signals Testing Suite
包含单元测试、集成测试、性能测试和数据质量验证
"""

import unittest
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import yaml

import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# 导入要测试的模块
from src.non_price.signal_data_manager import (
    NonPriceSignal, SignalQualityMetrics, EnhancedSignalDataManager,
    SignalDataQualityValidator
)
from src.non_price.signal_conversion_engine import (
    TechnicalIndicatorSignal, SignalConversionEngine, get_conversion_engine
)
from src.optimization.sr_mdd_optimizer import (
    SRMDDOptimizer, OptimizationParameters, OptimizationResult
)


class TestSignalDataQualityValidator(unittest.TestCase):
    """信号数据质量验证器测试"""

    def setUp(self):
        self.config = {
            'quality_thresholds': {
                'min_completeness': 0.9,
                'min_accuracy': 0.95,
                'min_timeliness': 0.8,
                'min_consistency': 0.9,
                'min_overall_score': 0.85
            }
        }
        self.validator = SignalDataQualityValidator(self.config)

    def test_valid_signal_batch(self):
        """测试有效信号批次验证"""
        # 创建测试信号
        now = datetime.now()
        signals = [
            NonPriceSignal(
                signal_id="test_1",
                signal_type="hibor",
                source="test",
                timestamp=now - timedelta(hours=1),
                value=3.5,
                confidence=0.95,
                metadata={}
            ),
            NonPriceSignal(
                signal_id="test_2",
                signal_type="hibor",
                source="test",
                timestamp=now - timedelta(hours=2),
                value=3.6,
                confidence=0.9,
                metadata={}
            )
        ]

        # 验证信号质量
        metrics = self.validator.validate_signal_batch(signals)

        # 验证结果
        self.assertIsInstance(metrics, SignalQualityMetrics)
        self.assertEqual(metrics.completeness, 1.0)
        self.assertEqual(metrics.accuracy, 1.0)
        self.assertEqual(metrics.timeliness, 1.0)
        self.assertEqual(metrics.consistency, 1.0)
        self.assertEqual(metrics.overall_score, 1.0)
        self.assertEqual(len(metrics.issues), 0)

    def test_empty_signal_batch(self):
        """测试空信号批次"""
        metrics = self.validator.validate_signal_batch([])

        self.assertEqual(metrics.completeness, 0.0)
        self.assertEqual(metrics.accuracy, 0.0)
        self.assertEqual(metrics.timeliness, 0.0)
        self.assertEqual(metrics.consistency, 0.0)
        self.assertEqual(metrics.overall_score, 0.0)
        self.assertIn("No signals provided", metrics.issues[0])

    def test_out_of_range_values(self):
        """测试超出范围的数值"""
        now = datetime.now()
        signals = [
            NonPriceSignal(
                signal_id="test_1",
                signal_type="hibor",  # HIBOR正常范围0-20%
                source="test",
                timestamp=now,
                value=25.0,  # 超出范围
                confidence=0.95,
                metadata={}
            )
        ]

        metrics = self.validator.validate_signal_batch(signals)

        self.assertLess(metrics.accuracy, 1.0)
        self.assertGreater(len(metrics.issues), 0)
        self.assertTrue(any("Out of range value" in issue for issue in metrics.issues))

    def test_stale_data(self):
        """测试过期数据"""
        old_time = datetime.now() - timedelta(hours=30)  # 超过24小时
        signals = [
            NonPriceSignal(
                signal_id="test_1",
                signal_type="hibor",
                source="test",
                timestamp=old_time,
                value=3.5,
                confidence=0.95,
                metadata={}
            )
        ]

        metrics = self.validator.validate_signal_batch(signals)

        self.assertLess(metrics.timeliness, 1.0)
        self.assertGreater(len(metrics.issues), 0)
        self.assertTrue(any("Stale data" in issue for issue in metrics.issues))

    def test_inconsistent_data(self):
        """测试不一致的数据"""
        now = datetime.now()
        signals = [
            NonPriceSignal(
                signal_id="test_1",
                signal_type="hibor",
                source="test",
                timestamp=now - timedelta(hours=1),
                value=3.5,
                confidence=0.95,
                metadata={}
            ),
            NonPriceSignal(
                signal_id="test_2",
                signal_type="hibor",
                source="test",
                timestamp=now - timedelta(hours=2),
                value=10.0,  # 变化过大
                confidence=0.9,
                metadata={}
            )
        ]

        metrics = self.validator.validate_signal_batch(signals)

        self.assertLess(metrics.consistency, 1.0)
        self.assertGreater(len(metrics.issues), 0)


class TestSignalConversionEngine(unittest.TestCase):
    """信号转换引擎测试"""

    def setUp(self):
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"

        config = {
            'conversion_rules': {
                'hibor': {
                    'indicators': ['RSI', 'MACD'],
                    'rsi': {'timeperiods': [14]},
                    'macd': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}
                }
            },
            'preprocessing': {
                'missing_values': {'method': 'forward_fill'},
                'outliers': {'method': 'iqr', 'threshold': 1.5, 'action': 'clip'},
                'smoothing': {'method': 'exponential', 'alpha': 0.3},
                'normalization': {'method': 'zscore'}
            }
        }

        with open(self.config_path, 'w') as f:
            yaml.dump(config, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_rsi_generation(self):
        """测试RSI指标生成"""
        # 创建测试信号数据
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        values = np.random.normal(4.0, 0.5, 100)  # 模拟HIBOR数据
        signal_data = pd.Series(values, index=dates)

        # 模拟信号管理器
        mock_signal_manager = Mock()
        mock_signal_manager.get_signal_data.return_value = []

        with patch('src.non_price.signal_conversion_engine.get_signal_manager', return_value=mock_signal_manager):
            engine = SignalConversionEngine(str(self.config_path))

            # 直接测试指标生成器
            indicator_configs = {'rsi': {'timeperiods': [14]}}
            indicators = engine.indicator_generator.generate_indicators(
                signal_data, 'hibor', indicator_configs
            )

            # 验证结果
            self.assertGreater(len(indicators), 0)
            rsi_indicators = [ind for ind in indicators if ind.indicator_type == 'RSI']
            self.assertEqual(len(rsi_indicators), 1)

            rsi_indicator = rsi_indicators[0]
            self.assertEqual(rsi_indicator.source_signal_type, 'hibor')
            self.assertIn('timeperiod', rsi_indicator.parameters)
            self.assertEqual(rsi_indicator.parameters['timeperiod'], 14)
            self.assertGreater(len(rsi_indicator.values), 0)

    def test_macd_generation(self):
        """测试MACD指标生成"""
        # 创建测试信号数据
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        values = np.cumsum(np.random.normal(0, 1, 100)) + 100  # 模拟价格趋势
        signal_data = pd.Series(values, index=dates)

        # 模拟信号管理器
        mock_signal_manager = Mock()
        mock_signal_manager.get_signal_data.return_value = []

        with patch('src.non_price.signal_conversion_engine.get_signal_manager', return_value=mock_signal_manager):
            engine = SignalConversionEngine(str(self.config_path))

            # 直接测试指标生成器
            indicator_configs = {'macd': {'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}}
            indicators = engine.indicator_generator.generate_indicators(
                signal_data, 'monetary_base', indicator_configs
            )

            # 验证结果
            macd_indicators = [ind for ind in indicators if ind.indicator_type == 'MACD']
            self.assertGreater(len(macd_indicators), 0)

            # 验证MACD包含多个子指标
            indicator_ids = [ind.indicator_id for ind in macd_indicators]
            self.assertTrue(any('MACD' in id_ for id_ in indicator_ids))
            self.assertTrue(any('MACD_Signal' in id_ for id_ in indicator_ids))
            self.assertTrue(any('MACD_Histogram' in id_ for id_ in indicator_ids))

    def test_signal_preprocessing(self):
        """测试信号预处理"""
        # 创建包含缺失值和异常值的测试数据
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        values = np.random.normal(4.0, 0.5, 50)

        # 添加缺失值
        values[10:12] = np.nan

        # 添加异常值
        values[20] = 20.0  # 异常大的值

        signal_data = pd.Series(values, index=dates)

        # 模拟信号管理器
        mock_signal_manager = Mock()
        mock_signal_manager.get_signal_data.return_value = []

        with patch('src.non_price.signal_conversion_engine.get_signal_manager', return_value=mock_signal_manager):
            engine = SignalConversionEngine(str(self.config_path))

            # 创建测试信号
            signals = []
            for i, (date, value) in enumerate(zip(dates, values)):
                if not np.isnan(value):
                    signal = NonPriceSignal(
                        signal_id=f"test_{i}",
                        signal_type="hibor",
                        source="test",
                        timestamp=date,
                        value=value,
                        confidence=0.95,
                        metadata={}
                    )
                    signals.append(signal)

            # 执行预处理
            processed_data = engine.preprocessor.preprocess_signals(signals, "hibor")

            # 验证结果
            self.assertFalse(processed_data.isnull().any())  # 不应该有缺失值
            self.assertLess(processed_data.max(), 10.0)  # 异常值应该被裁剪

    def test_signal_fusion(self):
        """测试信号融合"""
        # 创建多个测试指标
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')

        indicators = [
            TechnicalIndicatorSignal(
                indicator_id="rsi_14",
                indicator_type="RSI",
                source_signal_type="hibor",
                parameters={'timeperiod': 14},
                values=pd.Series(np.random.uniform(30, 70, 50), index=dates),
                signal_strength=0.8,
                generation_time=datetime.now(),
                confidence=0.9,
                metadata={}
            ),
            TechnicalIndicatorSignal(
                indicator_id="macd",
                indicator_type="MACD",
                source_signal_type="hibor",
                parameters={'fastperiod': 12},
                values=pd.Series(np.random.uniform(-0.5, 0.5, 50), index=dates),
                signal_strength=0.7,
                generation_time=datetime.now(),
                confidence=0.85,
                metadata={}
            )
        ]

        # 模拟信号管理器
        mock_signal_manager = Mock()
        mock_signal_manager.get_signal_data.return_value = []

        with patch('src.non_price.signal_conversion_engine.get_signal_manager', return_value=mock_signal_manager):
            engine = SignalConversionEngine(str(self.config_path))

            # 执行信号融合
            fused_indicator = engine.fusion_engine.fuse_signals(indicators, 'weighted_average')

            # 验证结果
            self.assertEqual(fused_indicator.indicator_type, "Fused")
            self.assertEqual(fused_indicator.source_signal_type, "multiple")
            self.assertIn('source_indicators', fused_indicator.parameters)
            self.assertEqual(len(fused_indicator.parameters['source_indicators']), 2)
            self.assertGreater(len(fused_indicator.values), 0)


class TestSRMDDOptimizer(unittest.TestCase):
    """SR/MDD优化器测试"""

    def setUp(self):
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_srmdd_config.yaml"

        config = {
            'objectives': {
                'sortino_ratio': {'weight': 0.7, 'target': 1.5, 'min_acceptable': 1.0},
                'max_dd_duration': {'weight': 0.3, 'target': 60, 'max_acceptable': 180},
                'win_rate': {'weight': 0.1, 'target': 0.55, 'min_acceptable': 0.45}
            },
            'optimization': {
                'search_algorithm': 'random',
                'max_iterations': 10  # 减少测试时间
            },
            'backtesting': {
                'init_cash': 1000000,
                'fees': 0.001,
                'slippage': 0.001
            }
        }

        with open(self.config_path, 'w') as f:
            yaml.dump(config, f)

        # 创建测试价格数据
        self.dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
        np.random.seed(42)  # 确保可重复性

        # 生成模拟价格数据
        returns = np.random.normal(0.0005, 0.02, 252)  # 日收益率
        prices = 100 * np.cumprod(1 + returns)

        self.price_data = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, 252)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, 252))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, 252))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 252)
        }, index=self.dates)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_sortino_ratio_calculation(self):
        """测试Sortino比率计算"""
        from src.optimization.sr_mdd_optimizer import PerformanceCalculator

        # 创建测试收益率序列
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))

        # 计算Sortino比率
        sortino = PerformanceCalculator.calculate_sortino_ratio(returns)

        # 验证结果合理性
        self.assertIsInstance(sortino, float)
        self.assertGreaterEqual(sortino, 0)  # 平均收益为正时Sortino应该为正

    def test_max_dd_duration_calculation(self):
        """测试最大回撤持续时间计算"""
        from src.optimization.sr_mdd_optimizer import PerformanceCalculator

        # 创建包含回撤的测试收益率序列
        returns = pd.Series([
            0.01, 0.02, -0.01, -0.02, -0.01,  # 回撤开始
            -0.01, -0.005, 0.01, 0.02,        # 回撤结束
            0.01, 0.015, -0.005, -0.01,       # 另一个回撤
            -0.005, 0.005, 0.01, 0.015
        ])

        max_dd_duration = PerformanceCalculator.calculate_max_dd_duration(returns)

        # 验证结果合理性
        self.assertIsInstance(max_dd_duration, int)
        self.assertGreaterEqual(max_dd_duration, 0)

    def test_single_parameter_evaluation(self):
        """测试单个参数评估"""
        # 创建测试指标
        dates = self.dates[:-50]  # 留出一些空间用于信号生成
        indicators = [
            TechnicalIndicatorSignal(
                indicator_id="test_rsi",
                indicator_type="RSI",
                source_signal_type="hibor",
                parameters={'timeperiod': 14},
                values=pd.Series(np.random.uniform(20, 80, len(dates)), index=dates),
                signal_strength=0.8,
                generation_time=datetime.now(),
                confidence=0.9,
                metadata={}
            )
        ]

        # 创建测试参数
        params = OptimizationParameters(
            signal_type="hibor",
            indicator_type="RSI",
            parameters={
                'buy_threshold': 0.6,
                'sell_threshold': 0.4,
                'normalization_scale': 1.0,
                'normalization_offset': 0.0
            },
            weights={'RSI': 1.0},
            constraints={}
        )

        # 模拟转换引擎
        mock_conversion_engine = Mock()
        mock_conversion_engine.convert_signals_to_indicators.return_value = {'hibor': indicators}

        with patch('src.optimization.sr_mdd_optimizer.get_conversion_engine', return_value=mock_conversion_engine):
            optimizer = SRMDDOptimizer(str(self.config_path))

            # 评估单个参数
            result = optimizer.multi_objective_optimizer._evaluate_single_candidate(
                params, indicators, self.price_data
            )

            # 验证结果
            self.assertIsInstance(result, OptimizationResult)
            self.assertEqual(result.parameters, params)
            self.assertIsInstance(result.sortino_ratio, float)
            self.assertIsInstance(result.max_dd_duration, int)
            self.assertGreaterEqual(result.sortino_ratio, 0)
            self.assertGreaterEqual(result.max_dd_duration, 0)

    def test_pareto_optimal_selection(self):
        """测试Pareto最优解选择"""
        from src.optimization.sr_mdd_optimizer import OptimizationParameters

        # 创建测试结果
        results = [
            OptimizationResult(
                parameters=OptimizationParameters("hibor", "RSI", {}, {}, {}),
                sortino_ratio=1.5, max_dd_duration=60, sharpe_ratio=1.2,
                total_return=0.15, win_rate=0.55, max_drawdown=-0.08,
                volatility=0.18, calmar_ratio=1.875, optimization_time=1.0,
                backtest_stats={}, confidence_score=0.8
            ),
            OptimizationResult(
                parameters=OptimizationParameters("hibor", "RSI", {}, {}, {}),
                sortino_ratio=1.8, max_dd_duration=80, sharpe_ratio=1.4,
                total_return=0.18, win_rate=0.58, max_drawdown=-0.10,
                volatility=0.20, calmar_ratio=1.8, optimization_time=1.0,
                backtest_stats={}, confidence_score=0.85
            ),
            OptimizationResult(
                parameters=OptimizationParameters("hibor", "RSI", {}, {}, {}),
                sortino_ratio=1.2, max_dd_duration=40, sharpe_ratio=1.0,
                total_return=0.12, win_rate=0.52, max_drawdown=-0.06,
                volatility=0.15, calmar_ratio=2.0, optimization_time=1.0,
                backtest_stats={}, confidence_score=0.75
            ),
            # 被支配的解
            OptimizationResult(
                parameters=OptimizationParameters("hibor", "RSI", {}, {}, {}),
                sortino_ratio=1.0, max_dd_duration=100, sharpe_ratio=0.8,
                total_return=0.10, win_rate=0.48, max_drawdown=-0.12,
                volatility=0.22, calmar_ratio=0.83, optimization_time=1.0,
                backtest_stats={}, confidence_score=0.7
            )
        ]

        # 模拟转换引擎
        mock_conversion_engine = Mock()
        mock_conversion_engine.convert_signals_to_indicators.return_value = {}

        with patch('src.optimization.sr_mdd_optimizer.get_conversion_engine', return_value=mock_conversion_engine):
            optimizer = SRMDDOptimizer(str(self.config_path))

            # 找到Pareto最优解
            pareto_solutions = optimizer.multi_objective_optimizer._find_pareto_optimal(results)

            # 验证结果
            self.assertLessEqual(len(pareto_solutions), len(results))

            # 验证Pareto最优解的排名
            for solution in pareto_solutions:
                self.assertIsNotNone(solution.pareto_rank)
                self.assertGreaterEqual(solution.pareto_rank, 1)

    def test_parameter_space_generation(self):
        """测试参数空间生成"""
        parameter_space = {
            'signal_type': 'hibor',
            'buy_threshold': {'range': [0.5, 0.8, 0.1]},
            'sell_threshold': {'range': [0.2, 0.5, 0.1]},
            'weights': {
                'RSI': {'values': [0.5, 0.7, 1.0]},
                'MACD': {'values': [0.3, 0.5, 0.8]}
            }
        }

        # 模拟转换引擎
        mock_conversion_engine = Mock()
        mock_conversion_engine.convert_signals_to_indicators.return_value = {}

        with patch('src.optimization.sr_mdd_optimizer.get_conversion_engine', return_value=mock_conversion_engine):
            optimizer = SRMDDOptimizer(str(self.config_path))

            # 生成网格搜索候选
            candidates = optimizer.multi_objective_optimizer._generate_grid_search_candidates(parameter_space)

            # 验证结果
            self.assertGreater(len(candidates), 0)

            # 验证参数范围
            for candidate in candidates:
                self.assertGreaterEqual(candidate.parameters['buy_threshold'], 0.5)
                self.assertLessEqual(candidate.parameters['buy_threshold'], 0.8)
                self.assertGreaterEqual(candidate.parameters['sell_threshold'], 0.2)
                self.assertLessEqual(candidate.parameters['sell_threshold'], 0.5)
                self.assertIn(candidate.parameters['weights']['RSI'], [0.5, 0.7, 1.0])
                self.assertIn(candidate.parameters['weights']['MACD'], [0.3, 0.5, 0.8])


class TestIntegrationWorkflow(unittest.TestCase):
    """集成测试：端到端工作流测试"""

    def setUp(self):
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_integration_config.yaml"

        config = {
            'conversion_rules': {
                'hibor': {
                    'indicators': ['RSI'],
                    'rsi': {'timeperiods': [14]}
                }
            },
            'preprocessing': {
                'missing_values': {'method': 'forward_fill'},
                'normalization': {'method': 'zscore'}
            },
            'objectives': {
                'sortino_ratio': {'weight': 0.7, 'target': 1.0, 'min_acceptable': 0.5},
                'max_dd_duration': {'weight': 0.3, 'target': 90, 'max_acceptable': 180}
            }
        }

        with open(self.config_path, 'w') as f:
            yaml.dump(config, f)

        # 创建测试数据
        self.dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        np.random.seed(42)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_end_to_end_optimization(self):
        """端到端优化测试"""
        # 模拟完整的优化流程
        signal_types = ['hibor']

        # 创建测试价格数据
        prices = 100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, len(self.dates)))
        price_data = pd.DataFrame({
            'close': prices,
            'open': prices * (1 + np.random.normal(0, 0.005, len(prices))),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, len(prices)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(prices)))),
            'volume': np.random.randint(1000000, 10000000, len(prices))
        }, index=self.dates)

        # 创建模拟信号
        hibor_values = np.random.normal(4.0, 0.5, len(self.dates))
        mock_signals = [
            NonPriceSignal(
                signal_id=f"hibor_{i}",
                signal_type="hibor",
                source="mock",
                timestamp=date,
                value=float(value),
                confidence=0.9,
                metadata={}
            )
            for i, (date, value) in enumerate(zip(self.dates, hibor_values))
        ]

        # 模拟信号管理器和转换引擎
        with patch('src.non_price.signal_data_manager.get_signal_manager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.get_signal_data.return_value = mock_signals
            mock_manager.return_value = mock_manager_instance

            with patch('src.optimization.sr_mdd_optimizer.get_conversion_engine') as mock_conversion:
                # 创建模拟指标
                indicators = [
                    TechnicalIndicatorSignal(
                        indicator_id="hibor_rsi_14",
                        indicator_type="RSI",
                        source_signal_type="hibor",
                        parameters={'timeperiod': 14},
                        values=pd.Series(np.random.uniform(20, 80, len(self.dates)), index=self.dates),
                        signal_strength=0.8,
                        generation_time=datetime.now(),
                        confidence=0.9,
                        metadata={}
                    )
                ]

                mock_conversion_instance = Mock()
                mock_conversion_instance.convert_signals_to_indicators.return_value = {'hibor': indicators}
                mock_conversion.return_value = mock_conversion_instance

                # 执行优化
                optimizer = SRMDDOptimizer(str(self.config_path))
                parameter_space = optimizer._get_default_parameter_space()
                parameter_space['max_iterations'] = 5  # 减少测试时间

                results = optimizer.optimize(
                    signal_types, price_data, parameter_space, "random"
                )

                # 验证结果
                self.assertGreater(len(results), 0)

                for result in results:
                    self.assertIsInstance(result, OptimizationResult)
                    self.assertIsInstance(result.sortino_ratio, float)
                    self.assertIsInstance(result.max_dd_duration, int)
                    self.assertGreaterEqual(result.sortino_ratio, 0)
                    self.assertGreaterEqual(result.max_dd_duration, 0)

    def test_configuration_validation(self):
        """测试配置验证"""
        # 测试有效配置
        optimizer = SRMDDOptimizer(str(self.config_path))
        self.assertIsNotNone(optimizer.config)
        self.assertIn('objectives', optimizer.config)

        # 测试无效配置
        invalid_config_path = Path(self.temp_dir) / "invalid_config.yaml"
        with open(invalid_config_path, 'w') as f:
            f.write("invalid: yaml: content:")

        # 应该回退到默认配置
        optimizer_invalid = SRMDDOptimizer(str(invalid_config_path))
        self.assertIsNotNone(optimizer_invalid.config)
        self.assertIn('objectives', optimizer_invalid.config)


class TestPerformanceValidation(unittest.TestCase):
    """性能测试"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_perf_config.yaml"

        config = {
            'conversion_rules': {
                'hibor': {
                    'indicators': ['RSI', 'MACD'],
                    'rsi': {'timeperiods': [14, 21]},
                    'macd': {'fastperiod': 12, 'slowperiod': 26}
                }
            },
            'optimization': {
                'max_iterations': 5  # 减少测试时间
            }
        }

        with open(self.config_path, 'w') as f:
            yaml.dump(config, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_signal_processing_performance(self):
        """测试信号处理性能"""
        import time

        # 创建大量测试数据
        dates = pd.date_range(start='2020-01-01', periods=1000, freq='D')
        values = np.random.normal(4.0, 0.5, 1000)

        start_time = time.time()

        # 模拟信号管理器
        mock_signals = [
            NonPriceSignal(
                signal_id=f"test_{i}",
                signal_type="hibor",
                source="test",
                timestamp=date,
                value=float(value),
                confidence=0.9,
                metadata={}
            )
            for i, (date, value) in enumerate(zip(dates, values))
        ]

        with patch('src.non_price.signal_data_manager.get_signal_manager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.get_signal_data.return_value = mock_signals
            mock_manager.return_value = mock_manager_instance

            engine = SignalConversionEngine(str(self.config_path))
            processing_time = time.time() - start_time

            # 验证性能
            self.assertLess(processing_time, 10.0)  # 应该在10秒内完成

    def test_parallel_optimization_performance(self):
        """测试并行优化性能"""
        import time

        # 创建多个优化任务
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []

            for i in range(4):
                # 模拟优化引擎
                mock_conversion_engine = Mock()
                mock_conversion_engine.convert_signals_to_indicators.return_value = {}

                with patch('src.optimization.sr_mdd_optimizer.get_conversion_engine', return_value=mock_conversion_engine):
                    optimizer = SRMDDOptimizer(str(self.config_path))
                    future = executor.submit(optimizer._get_default_parameter_space)
                    futures.append(future)

            start_time = time.time()
            results = [future.result() for future in futures]
            total_time = time.time() - start_time

            # 验证结果和性能
            self.assertEqual(len(results), 4)
            self.assertLess(total_time, 5.0)  # 并行执行应该很快


def run_performance_benchmarks():
    """运行性能基准测试"""
    print("Running performance benchmarks...")

    # 测试数据处理性能
    test_instance = TestPerformanceValidation()
    test_instance.setUp()

    try:
        test_instance.test_signal_processing_performance()
        test_instance.test_parallel_optimization_performance()
        print("✓ All performance benchmarks passed")
    finally:
        test_instance.tearDown()


def run_integration_tests():
    """运行集成测试"""
    print("Running integration tests...")

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加集成测试
    test_suite.addTest(TestIntegrationWorkflow('test_end_to_end_optimization'))
    test_suite.addTest(TestIntegrationWorkflow('test_configuration_validation'))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result.wasSuccessful()


def run_all_tests():
    """运行所有测试"""
    print("Running comprehensive test suite for non-price signals system...")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    test_classes = [
        TestSignalDataQualityValidator,
        TestSignalConversionEngine,
        TestSRMDDOptimizer,
        TestIntegrationWorkflow,
        TestPerformanceValidation
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 运行性能基准测试
    print("\n" + "=" * 60)
    run_performance_benchmarks()

    # 输出总结
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    if result.wasSuccessful():
        print("\n✓ All tests passed successfully!")
        return True
    else:
        print("\n✗ Some tests failed!")
        return False


if __name__ == '__main__':
    # 运行所有测试
    success = run_all_tests()
    exit(0 if success else 1)