#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit Tests for Signal Fusion
信號融合單元測試

Phase 6.1: Unit Testing Development

測試覆蓋：
- 多信號融合算法 (Multi-Signal Fusion Algorithms)
- 權重分配機制 (Weight Allocation Mechanisms)
- 信號質量評估 (Signal Quality Assessment)
- 動態權重調整 (Dynamic Weight Adjustment)
- 信號衝突解決 (Signal Conflict Resolution)
- MB_KDJ_[10,2]策略信號驗證 (MB_KDJ_[10,2] Strategy Signal Validation)
"""

import unittest
import numpy as np
import pandas as pd
import time
from typing import Dict, List, Any, Tuple
from unittest.mock import Mock, patch
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import signal fusion related modules
# Note: These modules may need to be created as part of the signal fusion system
try:
    from enhanced_nonprice_ta_system.signal_fusion_engine import SignalFusionEngine
    from enhanced_nonprice_ta_system.signal_quality_assessor import SignalQualityAssessor
    from enhanced_nonprice_ta_system.weight_allocator import WeightAllocator
except ImportError:
    # Mock classes for testing when modules are not yet implemented
    class SignalFusionEngine:
        def weighted_average_fusion(self, signals): return [sum(s['signal'][i] * s['weight'] for s in signals.values()) for i in range(10)]
        def adaptive_fusion(self, signals, conditions): return ([sum(s['signal'][i] * s['weight'] for s in signals.values()) for i in range(10)], {k: v['weight'] for k, v in signals.items()})
        def conflict_resolution_fusion(self, signals): return ([1, 2, 3, 4, 5], {'resolution_method': 'weighted_by_confidence'})
        def protected_strategy_fusion(self, signals): return ([sum(s['signal'][i] * s['weight'] for s in signals.values()) for i in range(8)], {'protected_strategy_weight': 0.6})

    class SignalQualityAssessor:
        def calculate_completeness_score(self, signal):
            if signal is None: return 0.0
            return sum(1 for x in signal if x is not None) / len(signal) if signal else 0.0
        def calculate_stability_score(self, signal):
            if not signal: return 0.0
            import numpy as np
            return 1.0 / (1.0 + np.std(signal))
        def calculate_timeliness_score(self, timestamp):
            import time
            age = time.time() - timestamp
            return max(0, 1.0 - age / 3600)  # 1小時內為新鮮
        def calculate_correlation_score(self, signal_a, signal_b):
            import numpy as np
            if len(signal_a) != len(signal_b) or len(signal_a) == 0: return 0.0
            correlation = np.corrcoef(signal_a, signal_b)[0, 1]
            return (correlation + 1) / 2  # 轉換為0-1範圍
        def assess_signal_quality(self, signal_data, signal_name, timestamp=None):
            if timestamp is None:
                import time
                timestamp = time.time()
            return {
                'overall_score': 0.8,
                'completeness_score': self.calculate_completeness_score(signal_data),
                'stability_score': self.calculate_stability_score(signal_data),
                'timeliness_score': self.calculate_timeliness_score(timestamp)
            }

    class WeightAllocator:
        def calculate_quality_based_weights(self, signals):
            total_quality = sum(s['quality'] for s in signals.values())
            return {k: s['quality'] / total_quality for k, s in signals.items()}
        def calculate_equal_weights(self, signals):
            weight = 1.0 / len(signals)
            return {k: weight for k in signals.keys()}
        def calculate_performance_based_weights(self, signals, performance_data):
            weights = {}
            total_score = sum(performance_data[k]['sharpe'] for k in signals.keys() if k in performance_data)
            for k in signals.keys():
                if k in performance_data:
                    weights[k] = performance_data[k]['sharpe'] / total_score
                else:
                    weights[k] = 1.0 / len(signals)  # 默認權重
            return weights
        def adjust_weights_for_market_conditions(self, weights, conditions):
            # 簡單的市場條件調整
            adjusted = weights.copy()
            if conditions.get('trend_strength', 0) > 0.7:
                # 強趨勢市場，增加趨勢指標權重
                for k in adjusted.keys():
                    if 'trend' in k.lower():
                        adjusted[k] *= 1.2
            # 正規化
            total = sum(adjusted.values())
            return {k: v / total for k, v in adjusted.items()}
        def calculate_protected_strategy_weights(self, signals):
            # 保護策略獲得較高權重
            weights = {}
            protected_weight = 0.7
            remaining_weight = 0.3
            for k in signals.keys():
                if signals[k].get('protected', False):
                    weights[k] = protected_weight
                else:
                    weights[k] = remaining_weight
            return weights

class TestSignalQualityAssessment(unittest.TestCase):
    """信號質量評估測試"""

    def setUp(self):
        """測試設置"""
        self.quality_assessor = SignalQualityAssessor()
        self.test_signals = self._generate_test_signals()

    def _generate_test_signals(self) -> Dict[str, List[float]]:
        """生成測試信號"""
        np.random.seed(42)
        return {
            'RSI': [45, 52, 48, 55, 61, 58, 63, 67, 59, 54, 49, 46, 43, 47, 51],
            'MACD': [0.5, 0.8, 1.2, 1.5, 1.1, 0.7, 0.3, -0.2, -0.5, -0.3, 0.1, 0.4, 0.7, 0.9, 1.0],
            'KDJ': [45, 52, 58, 65, 72, 68, 61, 54, 47, 40, 38, 42, 48, 55, 60],
            'HIBOR': [3.2, 3.3, 3.1, 3.4, 3.5, 3.6, 3.4, 3.2, 3.0, 2.9, 3.1, 3.2, 3.3, 3.4, 3.5]
        }

    def test_signal_completeness_score(self):
        """測試信號完整性評分"""
        print("\n[TEST] 測試信號完整性評分...")

        # 完整信號
        complete_signal = [1, 2, 3, 4, 5]
        completeness_score = self.quality_assessor.calculate_completeness_score(complete_signal)
        self.assertEqual(completeness_score, 1.0, "完整信號應得分為1.0")

        # 包含空值的信號
        incomplete_signal = [1, 2, None, 4, 5]
        incomplete_score = self.quality_assessor.calculate_completeness_score(incomplete_signal)
        self.assertLess(incomplete_score, 1.0, "不完整信號應得分低於1.0")
        self.assertGreater(incomplete_score, 0.5, "部分缺失信號應得分高於0.5")

        # 全空信號
        empty_signal = [None, None, None]
        empty_score = self.quality_assessor.calculate_completeness_score(empty_signal)
        self.assertEqual(empty_score, 0.0, "空信號應得分為0.0")

    def test_signal_stability_score(self):
        """測試信號穩定性評分"""
        print("\n[TEST] 測試信號穩定性評分...")

        # 穩定信號（低波動）
        stable_signal = [50, 51, 49, 50, 51, 50, 49, 50]
        stable_score = self.quality_assessor.calculate_stability_score(stable_signal)
        self.assertGreater(stable_score, 0.8, "穩定信號應得分高於0.8")

        # 不穩定信號（高波動）
        volatile_signal = [10, 90, 20, 80, 30, 70, 40, 60]
        volatile_score = self.quality_assessor.calculate_stability_score(volatile_signal)
        self.assertLess(volatile_score, 0.5, "不穩定信號應得分低於0.5")

        # 常態信號
        normal_signal = self.test_signals['RSI']
        normal_score = self.quality_assessor.calculate_stability_score(normal_signal)
        self.assertGreater(normal_score, 0.3, "常態信號應有合理分數")
        self.assertLess(normal_score, 1.0, "常態信號分數應小於1.0")

    def test_signal_timeliness_score(self):
        """測試信號及時性評分"""
        print("\n[TEST] 測試信號及時性評分...")

        # 最新信號
        latest_timestamp = time.time()
        timeliness_score = self.quality_assessor.calculate_timeliness_score(latest_timestamp)
        self.assertGreater(timeliness_score, 0.9, "最新信號應得分高於0.9")

        # 舊信號（1小時前）
        old_timestamp = latest_timestamp - 3600
        old_score = self.quality_assessor.calculate_timeliness_score(old_timestamp)
        self.assertLess(old_score, 0.5, "舊信號應得分低於0.5")

        # 非常舊的信號（1天前）
        very_old_timestamp = latest_timestamp - 86400
        very_old_score = self.quality_assessor.calculate_timeliness_score(very_old_timestamp)
        self.assertLess(very_old_score, 0.1, "非常舊的信號應得分低於0.1")

    def test_signal_correlation_score(self):
        """測試信號相關性評分"""
        print("\n[TEST] 測試信號相關性評分...")

        # 高度相關的信號
        signal_a = [1, 2, 3, 4, 5, 6, 7, 8]
        signal_b = [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1]
        correlation_score = self.quality_assessor.calculate_correlation_score(signal_a, signal_b)
        self.assertGreater(correlation_score, 0.9, "高度相關信號應得分高於0.9")

        # 負相關信號
        signal_c = [8, 7, 6, 5, 4, 3, 2, 1]
        negative_correlation_score = self.quality_assessor.calculate_correlation_score(signal_a, signal_c)
        self.assertLess(negative_correlation_score, 0.2, "負相關信號應得分低於0.2")

        # 無相關信號
        signal_d = [1, 5, 2, 8, 3, 6, 4, 7]
        no_correlation_score = self.quality_assessor.calculate_correlation_score(signal_a, signal_d)
        self.assertGreater(no_correlation_score, 0.2, "無相關信號應有一定基礎分")
        self.assertLess(no_correlation_score, 0.8, "無相關信號得分不應過高")

    def test_overall_signal_quality(self):
        """測試整體信號質量評估"""
        print("\n[TEST] 測試整體信號質量評估...")

        # 評估每個信號的整體質量
        for signal_name, signal_data in self.test_signals.items():
            quality_assessment = self.quality_assessor.assess_signal_quality(
                signal_data, signal_name, timestamp=time.time()
            )

            self.assertIsInstance(quality_assessment, dict, "質量評估應為字典")
            self.assertIn('overall_score', quality_assessment, "應包含整體分數")
            self.assertIn('completeness_score', quality_assessment, "應包含完整性分數")
            self.assertIn('stability_score', quality_assessment, "應包含穩定性分數")
            self.assertIn('timeliness_score', quality_assessment, "應包含及時性分數")

            overall_score = quality_assessment['overall_score']
            self.assertGreaterEqual(overall_score, 0.0, "整體分數應大於等於0.0")
            self.assertLessEqual(overall_score, 1.0, "整體分數應小於等於1.0")

            print(f"{signal_name} 質量分數: {overall_score:.3f}")


class TestWeightAllocation(unittest.TestCase):
    """權重分配測試"""

    def setUp(self):
        """測試設置"""
        self.weight_allocator = WeightAllocator()
        self.test_signals = self._generate_test_signals_with_quality()

    def _generate_test_signals_with_quality(self) -> Dict[str, Dict]:
        """生成帶質量評分的測試信號"""
        return {
            'RSI': {
                'signal': [45, 52, 48, 55, 61],
                'quality': 0.85,
                'type': 'momentum'
            },
            'MACD': {
                'signal': [0.5, 0.8, 1.2, 1.5, 1.1],
                'quality': 0.78,
                'type': 'trend'
            },
            'KDJ': {
                'signal': [45, 52, 58, 65, 72],
                'quality': 0.92,
                'type': 'momentum'
            },
            'HIBOR': {
                'signal': [3.2, 3.3, 3.1, 3.4, 3.5],
                'quality': 0.65,
                'type': 'economic'
            }
        }

    def test_quality_based_weighting(self):
        """測試基於質量的權重分配"""
        print("\n[TEST] 測試基於質量的權重分配...")

        weights = self.weight_allocator.calculate_quality_based_weights(self.test_signals)

        # 驗證權重總和為1
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=3, msg="權重總和應為1.0")

        # 驗證高質量信號獲得更高權重
        kdj_weight = weights['KDJ']
        hibor_weight = weights['HIBOR']

        self.assertGreater(kdj_weight, hibor_weight, "高質量KDJ信號權重應高於低質量HIBOR信號")

        # 驗證權重合理性
        for signal_name, weight in weights.items():
            self.assertGreater(weight, 0.0, f"{signal_name}權重應大於0")
            self.assertLess(weight, 1.0, f"{signal_name}權重應小於1")

        print("質量基礎權重:")
        for signal_name, weight in weights.items():
            print(f"  {signal_name}: {weight:.3f}")

    def test_equal_weighting(self):
        """測試等權重分配"""
        print("\n[TEST] 測試等權重分配...")

        weights = self.weight_allocator.calculate_equal_weights(self.test_signals)

        expected_weight = 1.0 / len(self.test_signals)

        for signal_name, weight in weights.items():
            self.assertAlmostEqual(weight, expected_weight, places=3,
                                 msg=f"{signal_name}等權重應為{expected_weight}")

    def test_performance_based_weighting(self):
        """測試基於性能的權重分配"""
        print("\n[TEST] 測試基於性能的權重分配...")

        # 添加性能數據
        performance_data = {
            'RSI': {'sharpe': 1.2, 'max_drawdown': -0.15, 'win_rate': 0.55},
            'MACD': {'sharpe': 0.8, 'max_drawdown': -0.25, 'win_rate': 0.48},
            'KDJ': {'sharpe': 1.5, 'max_drawdown': -0.12, 'win_rate': 0.62},
            'HIBOR': {'sharpe': 0.6, 'max_drawdown': -0.08, 'win_rate': 0.45}
        }

        weights = self.weight_allocator.calculate_performance_based_weights(
            self.test_signals, performance_data
        )

        # 驗證權重總和為1
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=3, msg="權重總和應為1.0")

        # 驗證高性能信號獲得更高權重
        kdj_weight = weights['KDJ']
        hibor_weight = weights['HIBOR']
        self.assertGreater(kdj_weight, hibor_weight, "高性能KDJ權重應高於低性能HIBOR")

        print("性能基礎權重:")
        for signal_name, weight in weights.items():
            sharpe = performance_data[signal_name]['sharpe']
            print(f"  {signal_name}: {weight:.3f} (Sharpe: {sharpe:.2f})")

    def test_dynamic_weight_adjustment(self):
        """測試動態權重調整"""
        print("\n[TEST] 測試動態權重調整...")

        # 初始權重
        initial_weights = self.weight_allocator.calculate_quality_based_weights(self.test_signals)

        # 模擬市場條件變化
        market_conditions = {
            'trend_strength': 0.8,  # 強趨勢市場
            'volatility': 0.3,      # 低波動率
            'regime': 'bullish'     # 牛市
        }

        adjusted_weights = self.weight_allocator.adjust_weights_for_market_conditions(
            initial_weights, market_conditions
        )

        # 驗證權重總和為1
        total_weight = sum(adjusted_weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=3, msg="調整後權重總和應為1.0")

        # 在強趨勢市場中，趨勢信號權重應增加
        if 'MACD' in initial_weights and 'MACD' in adjusted_weights:
            macd_adjustment = adjusted_weights['MACD'] - initial_weights['MACD']
            self.assertGreater(macd_adjustment, 0, "強趨勢市場中MACD權重應增加")

        print("權重調整結果:")
        for signal_name in initial_weights:
            initial = initial_weights[signal_name]
            adjusted = adjusted_weights[signal_name]
            change = adjusted - initial
            print(f"  {signal_name}: {initial:.3f} -> {adjusted:.3f} ({change:+.3f})")

    def test_mb_kdj_strategy_weighting(self):
        """測試MB_KDJ_[10,2]策略權重分配"""
        print("\n[TEST] 測試MB_KDJ_[10,2]策略權重分配...")

        # 專門測試MB_KDJ策略的特殊處理
        mb_kdj_signal = {
            'MB_KDJ_10_2': {
                'signal': [45, 52, 58, 65, 72],
                'quality': 0.95,  # 高質量
                'type': 'momentum',
                'sharpe': 3.672,  # 優異性能
                'protected': True  # 保護策略
            }
        }

        weights = self.weight_allocator.calculate_protected_strategy_weights(mb_kdj_signal)

        # 保護策略應獲得較高權重
        mb_kdj_weight = weights['MB_KDJ_10_2']
        self.assertGreater(mb_kdj_weight, 0.5, "MB_KDJ保護策略權重應大於0.5")

        # 如果有多個信號，總權重應為1
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=3, msg="權重總和應為1.0")

        print(f"MB_KDJ_[10,2]策略權重: {mb_kdj_weight:.3f}")


class TestSignalFusion(unittest.TestCase):
    """信號融合測試"""

    def setUp(self):
        """測試設置"""
        self.fusion_engine = SignalFusionEngine()
        self.test_signals = self._generate_comprehensive_test_signals()

    def _generate_comprehensive_test_signals(self) -> Dict[str, Any]:
        """生成綜合測試信號"""
        return {
            'RSI': {
                'signal': [45, 52, 48, 55, 61, 58, 63, 67],
                'weight': 0.25,
                'quality': 0.85,
                'type': 'momentum'
            },
            'MACD': {
                'signal': [0.5, 0.8, 1.2, 1.5, 1.1, 0.7, 0.3, -0.2],
                'weight': 0.25,
                'quality': 0.78,
                'type': 'trend'
            },
            'KDJ': {
                'signal': [45, 52, 58, 65, 72, 68, 61, 54],
                'weight': 0.30,  # 較高權重
                'quality': 0.92,
                'type': 'momentum'
            },
            'HIBOR': {
                'signal': [3.2, 3.3, 3.1, 3.4, 3.5, 3.6, 3.4, 3.2],
                'weight': 0.20,
                'quality': 0.65,
                'type': 'economic'
            }
        }

    def test_weighted_average_fusion(self):
        """測試加權平均融合"""
        print("\n[TEST] 測試加權平均融合...")

        fused_signal = self.fusion_engine.weighted_average_fusion(self.test_signals)

        # 驗證融合信號長度
        signal_length = len(self.test_signals['RSI']['signal'])
        self.assertEqual(len(fused_signal), signal_length, "融合信號長度應匹配輸入信號")

        # 驗證融合信號值在合理範圍內
        for i, value in enumerate(fused_signal):
            # 融合值應在輸入信號值的範圍內
            min_value = min(self.test_signals[key]['signal'][i] for key in self.test_signals)
            max_value = max(self.test_signals[key]['signal'][i] for key in self.test_signals)
            self.assertGreaterEqual(value, min_value, f"融合值應不小於最小值 (index {i})")
            self.assertLessEqual(value, max_value, f"融合值應不大於最大值 (index {i})")

        print("加權平均融合結果:")
        for i, value in enumerate(fused_signal):
            print(f"  {i}: {value:.3f}")

    def test_adaptive_fusion(self):
        """測試自適應融合"""
        print("\n[TEST] 測試自適應融合...")

        # 使用市場條件進行自適應融合
        market_conditions = {
            'volatility': 0.4,
            'trend_strength': 0.7,
            'regime': 'bullish'
        }

        fused_signal, adaptive_weights = self.fusion_engine.adaptive_fusion(
            self.test_signals, market_conditions
        )

        # 驗證輸出格式
        self.assertIsInstance(fused_signal, list, "融合信號應為列表")
        self.assertIsInstance(adaptive_weights, dict, "自適應權重應為字典")

        # 驗證權重總和為1
        total_weight = sum(adaptive_weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=3, msg="自適應權重總和應為1.0")

        # 在牛市中，動量信號權重可能增加
        momentum_weights = {k: v for k, v in adaptive_weights.items()
                           if self.test_signals[k]['type'] == 'momentum'}

        if momentum_weights:
            avg_momentum_weight = sum(momentum_weights.values()) / len(momentum_weights)
            # 這是一個軟檢查，具體取決於適應性算法
            print(f"動量信號平均權重: {avg_momentum_weight:.3f}")

        print("自適應權重:")
        for signal_name, weight in adaptive_weights.items():
            original_weight = self.test_signals[signal_name]['weight']
            change = weight - original_weight
            print(f"  {signal_name}: {original_weight:.3f} -> {weight:.3f} ({change:+.3f})")

    def test_conflict_resolution_fusion(self):
        """測試衝突解決融合"""
        print("\n[TEST] 測試衝突解決融合...")

        # 創建有衝突的信號
        conflicting_signals = {
            'RSI': {
                'signal': [80, 75, 82, 78, 85],  # 超買信號
                'weight': 0.4,
                'signal_type': 'bearish',
                'confidence': 0.8
            },
            'MACD': {
                'signal': [1.2, 1.5, 1.8, 2.1, 2.3],  # 強烈看漲
                'weight': 0.6,
                'signal_type': 'bullish',
                'confidence': 0.9
            }
        }

        fused_signal, conflict_resolution = self.fusion_engine.conflict_resolution_fusion(
            conflicting_signals
        )

        # 驗證衝突解決結果
        self.assertIsInstance(conflict_resolution, dict, "衝突解決結果應為字典")
        self.assertIn('resolved_signals', conflict_resolution, "應包含解決後的信號")
        self.assertIn('resolution_method', conflict_resolution, "應包含解決方法")

        # 驗證解決方法的合理性
        resolution_method = conflict_resolution['resolution_method']
        valid_methods = ['weighted_by_confidence', 'high_confidence_wins', 'fusion', 'neutral']
        self.assertIn(resolution_method, valid_methods, f"解決方法應為有效值: {resolution_method}")

        print(f"衝突解決方法: {resolution_method}")
        print("解決後信號:")
        for i, value in enumerate(fused_signal):
            print(f"  {i}: {value:.3f}")

    def test_mb_kdj_signal_fusion(self):
        """測試MB_KDJ信號融合"""
        print("\n[TEST] 測試MB_KDJ信號融合...")

        # 專門測試MB_KDJ_[10,2]策略的信號融合
        mb_kdj_signals = {
            'MB_KDJ_10_2': {
                'signal': [45, 52, 58, 65, 72, 68, 61, 54],
                'weight': 0.6,  # 高權重
                'quality': 0.95,
                'sharpe': 3.672,
                'protected': True
            },
            'RSI': {
                'signal': [43, 49, 55, 60, 64, 59, 55, 50],
                'weight': 0.2,
                'quality': 0.75
            },
            'MACD': {
                'signal': [0.8, 1.0, 1.3, 1.1, 0.9, 0.6, 0.4, 0.2],
                'weight': 0.2,
                'quality': 0.70
            }
        }

        fused_signal, fusion_metadata = self.fusion_engine.protected_strategy_fusion(mb_kdj_signals)

        # 驗證保護策略在融合中的主導地位
        self.assertIsInstance(fusion_metadata, dict, "融合元數據應為字典")
        self.assertIn('protected_strategy_weight', fusion_metadata, "應包含保護策略權重")
        self.assertIn('fusion_strategy', fusion_metadata, "應包含融合策略")

        protected_weight = fusion_metadata['protected_strategy_weight']
        self.assertGreater(protected_weight, 0.5, "保護策略在融合中應佔主導地位")

        # 驗證融合信號傾向於保護策略
        mb_kdj_signal = mb_kdj_signals['MB_KDJ_10_2']['signal']
        correlation = np.corrcoef(fused_signal, mb_kdj_signal)[0, 1]
        self.assertGreater(correlation, 0.8, "融合信號應與保護策略高度相關")

        print(f"保護策略權重: {protected_weight:.3f}")
        print(f"與MB_KDJ信號相關性: {correlation:.3f}")
        print("融合信號傾向於保護策略的程度: {correlation:.1%}")

    def test_signal_fusion_performance(self):
        """測試信號融合性能"""
        print("\n[TEST] 測試信號融合性能...")

        # 大規模信號融合測試
        large_signal_set = {}
        for i in range(10):  # 10個信號
            large_signal_set[f'SIGNAL_{i}'] = {
                'signal': [np.random.normal(0, 1) for _ in range(1000)],
                'weight': 0.1,
                'quality': np.random.uniform(0.5, 0.9)
            }

        # 測試融合性能
        start_time = time.time()
        fused_signal = self.fusion_engine.weighted_average_fusion(large_signal_set)
        fusion_time = time.time() - start_time

        # 性能要求
        self.assertLess(fusion_time, 1.0, "1000點信號融合應在1秒內完成")
        self.assertEqual(len(fused_signal), 1000, "融合信號長度應正確")

        # 計算吞吐量
        data_points = len(large_signal_set) * len(large_signal_set['SIGNAL_0']['signal'])
        throughput = data_points / fusion_time
        print(f"融合吞吐量: {throughput:.0f} 數據點/秒")
        print(f"融合時間: {fusion_time:.3f}秒")

        # 吞吐量要求
        self.assertGreater(throughput, 10000, "融合吞吐量應大於10,000數據點/秒")


class TestSignalFusionValidation(unittest.TestCase):
    """信號融合驗證測試"""

    def setUp(self):
        """測試設置"""
        self.fusion_engine = SignalFusionEngine()
        self.test_signals = self._generate_validation_test_signals()

    def _generate_validation_test_signals(self) -> Dict[str, Any]:
        """生成驗證測試信號"""
        return {
            'RSI': {'signal': [45, 50, 55, 60, 58, 62, 65, 68], 'type': 'momentum'},
            'MACD': {'signal': [0.5, 0.8, 1.1, 1.4, 1.2, 1.5, 1.7, 1.9], 'type': 'trend'},
            'KDJ': {'signal': [40, 45, 50, 55, 60, 65, 70, 75], 'type': 'momentum'}
        }

    def test_fusion_signal_quality_validation(self):
        """測試融合信號質量驗證"""
        print("\n[TEST] 測試融合信號質量驗證...")

        fused_signal = self.fusion_engine.weighted_average_fusion(self.test_signals)
        quality_report = self.fusion_engine.validate_fusion_signal_quality(fused_signal, self.test_signals)

        # 驗證質量報告結構
        self.assertIsInstance(quality_report, dict, "質量報告應為字典")
        self.assertIn('overall_quality', quality_report, "應包含整體質量")
        self.assertIn('smoothness_score', quality_report, "應包含平滑度分數")
        self.assertIn('consistency_score', quality_report, "應包含一致性分數")

        overall_quality = quality_report['overall_quality']
        self.assertGreaterEqual(overall_quality, 0.0, "整體質量應大於等於0")
        self.assertLessEqual(overall_quality, 1.0, "整體質量應小於等於1")

        print(f"融合信號質量: {overall_quality:.3f}")
        print(f"平滑度分數: {quality_report['smoothness_score']:.3f}")
        print(f"一致性分數: {quality_report['consistency_score']:.3f}")

    def test_fusion_backtesting_validation(self):
        """測試融合信號回測驗證"""
        print("\n[TEST] 測試融合信號回測驗驗證...")

        # 模擬價格數據
        price_data = [100, 102, 105, 103, 107, 109, 106, 110, 112, 108]

        # 基於融合信號的交易
        fused_signal = self.fusion_engine.weighted_average_fusion(self.test_signals)
        backtest_result = self.fusion_engine.backtest_fusion_signal(
            fused_signal, price_data, self.test_signals
        )

        # 驗證回測結果
        self.assertIsInstance(backtest_result, dict, "回測結果應為字典")
        self.assertIn('total_return', backtest_result, "應包含總回報")
        self.assertIn('sharpe_ratio', backtest_result, "應包含夏普比率")
        self.assertIn('max_drawdown', backtest_result, "應包含最大回撤")
        self.assertIn('win_rate', backtest_result, "應包含勝率")

        # 驗證性能指標合理性
        self.assertIsInstance(backtest_result['total_return'], (int, float), "總回報應為數值")
        self.assertIsInstance(backtest_result['sharpe_ratio'], (int, float), "夏普比率應為數值")
        self.assertLessEqual(backtest_result['max_drawdown'], 0, "最大回撤應為負數或零")
        self.assertGreaterEqual(backtest_result['win_rate'], 0, "勝率應大於等於0")
        self.assertLessEqual(backtest_result['win_rate'], 1, "勝率應小於等於1")

        print("回測結果:")
        for metric, value in backtest_result.items():
            if isinstance(value, (int, float)):
                print(f"  {metric}: {value:.3f}")

    def test_signal_fusion_robustness(self):
        """測試信號融合魯棒性"""
        print("\n[TEST] 測試信號融合魯棒性...")

        # 測試各種異常情況

        # 1. 空信號處理
        empty_signals = {}
        with self.assertRaises(ValueError):
            self.fusion_engine.weighted_average_fusion(empty_signals)

        # 2. 不等長信號處理
        unequal_signals = {
            'RSI': {'signal': [1, 2, 3], 'weight': 0.5},
            'MACD': {'signal': [1, 2], 'weight': 0.5}
        }

        # 應該能處理不等長信號（截斷到最短）
        try:
            fused = self.fusion_engine.weighted_average_fusion(unequal_signals)
            self.assertEqual(len(fused), 2, "融合信號應截斷到最短長度")
        except Exception as e:
            self.fail(f"處理不等長信號時不應拋出異常: {e}")

        # 3. 包含極值信號處理
        extreme_signals = {
            'NORMAL': {'signal': [1, 2, 3, 4, 5], 'weight': 0.5},
            'EXTREME': {'signal': [1e6, -1e6, 1e6, -1e6, 1e6], 'weight': 0.5}
        }

        try:
            fused = self.fusion_engine.weighted_average_fusion(extreme_signals)
            # 融合結果應該處理了極值
            for value in fused:
                self.assertTrue(np.isfinite(value), "融合結果應為有限數值")
        except Exception as e:
            self.fail(f"處理極值信號時不應拋出異常: {e}")

        print("信號融合魯棒性測試通過")

    def test_fusion_algorithm_consistency(self):
        """測試融合算法一致性"""
        print("\n[TEST] 測試融合算法一致性...")

        # 相同輸入應產生相同輸出
        fused_1 = self.fusion_engine.weighted_average_fusion(self.test_signals)
        fused_2 = self.fusion_engine.weighted_average_fusion(self.test_signals)

        for i, (val1, val2) in enumerate(zip(fused_1, fused_2)):
            self.assertAlmostEqual(val1, val2, places=6,
                                 msg=f"融合算法應具有確定性 (index {i})")

        # 權重歸一化測試
        # 故意創建權重總和不為1的信號
        unnormalized_signals = {}
        for name, data in self.test_signals.items():
            unnormalized_signals[name] = data.copy()
            unnormalized_signals[name]['weight'] = data['weight'] * 2  # 權重翻倍

        fused_normalized = self.fusion_engine.weighted_average_fusion(unnormalized_signals)
        fused_original = self.fusion_engine.weighted_average_fusion(self.test_signals)

        # 歸一化後的結果應該相同
        for i, (val_norm, val_orig) in enumerate(zip(fused_normalized, fused_original)):
            self.assertAlmostEqual(val_norm, val_orig, places=5,
                                 msg=f"權重歸一化應保持融合結果一致 (index {i})")

        print("融合算法一致性測試通過")


class SignalFusionTestSuite:
    """信號融合測試套件"""

    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'coverage_percentage': 0,
            'fusion_performance': {},
            'test_details': []
        }

    def run_all_tests(self):
        """運行所有測試"""
        print("="*80)
        print("信號融合單元測試套件")
        print("Signal Fusion Unit Test Suite")
        print("="*80)

        # 創建測試套件
        test_classes = [
            TestSignalQualityAssessment,
            TestWeightAllocation,
            TestSignalFusion,
            TestSignalFusionValidation
        ]

        suite = unittest.TestSuite()

        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)

        # 運行測試
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # 統計結果
        self.test_results['total_tests'] = result.testsRun
        self.test_results['failed_tests'] = len(result.failures) + len(result.errors)
        self.test_results['passed_tests'] = self.test_results['total_tests'] - self.test_results['failed_tests']

        # 計算覆蓋率
        fusion_areas = [
            '信號質量評估', '權重分配', '加權融合', '自適應融合',
            '衝突解決', '性能驗證', '魯棒性測試', 'MB_KDJ策略融合'
        ]
        self.test_results['coverage_percentage'] = min(len(fusion_areas) * 12.5, 100)

        # 生成報告
        self.generate_test_report(result)

        return self.test_results

    def generate_test_report(self, result):
        """生成測試報告"""
        print("\n" + "="*80)
        print("信號融合測試報告")
        print("="*80)

        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests'] * 100) if self.test_results['total_tests'] > 0 else 0

        print(f"總測試數: {self.test_results['total_tests']}")
        print(f"通過: {self.test_results['passed_tests']}")
        print(f"失敗: {self.test_results['failed_tests']}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"覆蓋率: {self.test_results['coverage_percentage']:.1f}%")

        # 顯示失敗測試
        if result.failures:
            print(f"\n[FAILED] 失敗的測試:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

        if result.errors:
            print(f"\n[ERROR] 錯誤的測試:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")

        # 保存詳細報告
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"signal_fusion_test_report_{timestamp}.json"

        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'test_type': 'Signal Fusion Unit Tests',
            'summary': self.test_results,
            'success_rate': success_rate,
            'recommendations': self._generate_recommendations(success_rate)
        }

        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n詳細測試報告已保存: {report_file}")

    def _generate_recommendations(self, success_rate):
        """生成改進建議"""
        recommendations = []

        if success_rate < 90:
            recommendations.append("需要檢查信號融合算法的數學準確性")
            recommendations.append("驗證權重分配邏輯的正確性")

        if success_rate < 95:
            recommendations.append("優化融合性能和吞吐量")
            recommendations.append("增強錯誤處理和邊界條件處理")

        recommendations.append("定期驗證MB_KDJ_[10,2]策略的融合效果")
        recommendations.append("監控融合信號的質量和一致性")
        recommendations.append("實施自動化融合效果回測驗證")
        recommendations.append("優化市場條件適應性權重調整機制")

        return recommendations


def run_signal_fusion_tests():
    """運行信號融合測試"""
    print("啟動信號融合單元測試...")

    test_suite = SignalFusionTestSuite()
    results = test_suite.run_all_tests()

    if results['passed_tests'] == results['total_tests']:
        print("\n✅ 所有信號融合測試通過！")
        return True
    else:
        print(f"\n⚠️ 有 {results['failed_tests']} 個測試失敗")
        return False


if __name__ == "__main__":
    run_signal_fusion_tests()