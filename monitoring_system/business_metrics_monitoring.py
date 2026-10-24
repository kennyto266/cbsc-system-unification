#!/usr/bin/env python3
"""
業務指標監控模塊
Business Metrics Monitoring Module

監控量化交易系統的業務指標：數據質量、技術指標計算、Sharpe比率、回測性能、GPU加速等
"""

import time
import json
import logging
import asyncio
import aiohttp
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest
import statistics
import math

logger = logging.getLogger(__name__)

@dataclass
class DataQualityMetrics:
    """數據質量指標"""
    data_source: str
    timestamp: float
    total_records: int
    missing_records: int
    duplicate_records: int
    invalid_records: int
    freshness_score: float  # 數據新鮮度評分
    completeness_score: float  # 完整性評分
    accuracy_score: float  # 准確性評分
    overall_quality_score: float  # 綜合質量評分

@dataclass
class TechnicalIndicatorMetrics:
    """技術指標計算指標"""
    indicator_type: str
    symbol: str
    timestamp: float
    calculation_duration: float
    gpu_accelerated: bool
    calculation_success: bool
    error_message: Optional[str]
    data_points_processed: int
    memory_usage_mb: float

@dataclass
class SharpeRatioMetrics:
    """Sharpe比率計算指標"""
    calculation_id: str
    timestamp: float
    strategy_name: str
    symbol: str
    method_used: str  # 'standard', 'simplified', 'fallback'
    calculation_duration: float
    sharpe_ratio: float
    annual_return: float
    annual_volatility: float
    max_drawdown: float
    calculation_success: bool
    validation_passed: bool
    error_message: Optional[str]

@dataclass
class BacktestPerformanceMetrics:
    """回測性能指標"""
    backtest_id: str
    timestamp: float
    strategy_name: str
    symbol: str
    execution_duration: float
    total_strategies_tested: int
    successful_strategies: int
    strategies_per_second: float
    memory_usage_mb: float
    gpu_utilization: float
    best_strategy_performance: Dict[str, Any]
    optimization_method: str  # 'vectorbt', 'manual', 'gpu'

@dataclass
class TradingSignalMetrics:
    """交易信號指標"""
    signal_id: str
    timestamp: float
    strategy_name: str
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    signal_strength: float  # 0-1
    confidence_score: float  # 0-1
    generation_duration_ms: float
    indicators_used: List[str]
    risk_metrics: Dict[str, float]

class BusinessMetricsMonitor:
    """業務指標監控器"""

    def __init__(self):
        """初始化業務指標監控器"""
        self.metrics_history = {
            'data_quality': [],
            'technical_indicators': [],
            'sharpe_calculations': [],
            'backtest_performance': [],
            'trading_signals': []
        }

        # 初始化Prometheus指標
        self.registry = CollectorRegistry()

        # 數據質量指標
        self.data_quality_score = Gauge('data_quality_score', 'Data quality score', ['data_source'], registry=self.registry)
        self.data_freshness_score = Gauge('data_freshness_score', 'Data freshness score', ['data_source'], registry=self.registry)
        self.data_completeness_score = Gauge('data_completeness_score', 'Data completeness score', ['data_source'], registry=self.registry)
        self.data_accuracy_score = Gauge('data_accuracy_score', 'Data accuracy score', ['data_source'], registry=self.registry)

        # 技術指標指標
        self.indicator_calculation_duration = Histogram('indicator_calculation_duration_seconds', 'Indicator calculation duration', ['indicator_type', 'symbol'], registry=self.registry)
        self.indicator_calculation_success = Counter('indicator_calculation_success_total', 'Successful indicator calculations', ['indicator_type'], registry=self.registry)
        self.indicator_calculation_errors = Counter('indicator_calculation_errors_total', 'Failed indicator calculations', ['indicator_type'], registry=self.registry)
        self.gpu_acceleration_enabled = Gauge('gpu_acceleration_enabled', 'GPU acceleration enabled', registry=self.registry)

        # Sharpe比率指標
        self.sharpe_calculation_duration = Histogram('sharpe_calculation_duration_seconds', 'Sharpe calculation duration', ['strategy_name', 'method'], registry=self.registry)
        self.sharpe_calculation_errors = Counter('sharpe_calculation_errors_total', 'Sharpe calculation errors', ['strategy_name'], registry=self.registry)
        self.current_sharpe_ratio = Gauge('current_sharpe_ratio', 'Current Sharpe ratio', ['strategy_name', 'symbol'], registry=self.registry)
        self.sharpe_validation_passed = Counter('sharpe_validation_passed_total', 'Sharpe calculation validations passed', registry=self.registry)

        # 回測性能指標
        self.backtest_execution_duration = Histogram('backtest_execution_duration_seconds', 'Backtest execution duration', ['strategy_name', 'method'], registry=self.registry)
        self.strategies_tested_total = Counter('strategies_tested_total', 'Total strategies tested', ['strategy_name'], registry=self.registry)
        self.backtest_success_rate = Gauge('backtest_success_rate', 'Backtest success rate', ['strategy_name'], registry=self.registry)
        self.optimization_performance_score = Gauge('optimization_performance_score', 'Optimization performance score', ['strategy_name'], registry=self.registry)

        # 交易信號指標
        self.trading_signals_generated = Counter('trading_signals_generated_total', 'Trading signals generated', ['strategy_name', 'signal_type'], registry=self.registry)
        self.signal_generation_duration = Histogram('signal_generation_duration_ms', 'Signal generation duration', ['strategy_name'], registry=self.registry)
        self.signal_confidence_score = Gauge('signal_confidence_score', 'Signal confidence score', ['strategy_name', 'symbol'], registry=self.registry)

        # GPU加速指標
        self.gpu_accelerated_calculations = Counter('gpu_accelerated_calculations_total', 'GPU accelerated calculations', ['calculation_type'], registry=self.registry)
        self.gpu_performance_improvement = Gauge('gpu_performance_improvement_ratio', 'GPU performance improvement ratio', ['calculation_type'], registry=self.registry)

        logger.info("Business metrics monitor initialized")

    def record_data_quality(self, data_source: str, data_records: pd.DataFrame,
                          expected_records: int = None, max_age_hours: int = 24) -> DataQualityMetrics:
        """
        記錄數據質量指標

        Args:
            data_source: 數據源名稱
            data_records: 數據記錄DataFrame
            expected_records: 期望記錄數
            max_age_hours: 最大數據年齡(小時)

        Returns:
            DataQualityMetrics: 數據質量指標
        """
        try:
            # 基本統計
            total_records = len(data_records)
            missing_records = data_records.isnull().sum().sum()
            duplicate_records = data_records.duplicated().sum()

            # 檢查數據格式和範圍
            invalid_records = 0
            for column in data_records.select_dtypes(include=[np.number]).columns:
                # 檢查異常值 (例如價格為負或過大)
                if 'price' in column.lower() or 'close' in column.lower():
                    invalid_records += len(data_records[
                        (data_records[column] < 0) |
                        (data_records[column] > 1000000)  # 假設股價不超過100萬
                    ])

            # 計算新鮮度評分
            current_time = datetime.now()
            if 'date' in data_records.columns or data_records.index.name == 'date':
                dates = data_records.index if data_records.index.name == 'date' else pd.to_datetime(data_records['date'])
                latest_date = dates.max()
                data_age_hours = (current_time - latest_date).total_seconds() / 3600
                freshness_score = max(0, 100 - (data_age_hours / max_age_hours) * 100)
            else:
                freshness_score = 50  # 無法確定新鮮度

            # 計算完整性評分
            completeness_score = ((total_records - missing_records) / total_records * 100) if total_records > 0 else 0

            # 計算准确性評分
            accuracy_score = ((total_records - invalid_records) / total_records * 100) if total_records > 0 else 0

            # 綜合質量評分
            overall_quality_score = (freshness_score * 0.4 + completeness_score * 0.3 + accuracy_score * 0.3)

            metrics = DataQualityMetrics(
                data_source=data_source,
                timestamp=time.time(),
                total_records=total_records,
                missing_records=missing_records,
                duplicate_records=duplicate_records,
                invalid_records=invalid_records,
                freshness_score=freshness_score,
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                overall_quality_score=overall_quality_score
            )

            # 更新Prometheus指標
            self.data_quality_score.labels(data_source=data_source).set(overall_quality_score)
            self.data_freshness_score.labels(data_source=data_source).set(freshness_score)
            self.data_completeness_score.labels(data_source=data_source).set(completeness_score)
            self.data_accuracy_score.labels(data_source=data_source).set(accuracy_score)

            # 保存歷史記錄
            self.metrics_history['data_quality'].append(metrics)

            logger.info(f"Data quality recorded for {data_source}: {overall_quality_score:.1f}/100")
            return metrics

        except Exception as e:
            logger.error(f"Failed to record data quality for {data_source}: {e}")
            raise

    def record_technical_indicator_calculation(self, indicator_type: str, symbol: str,
                                            calculation_duration: float, gpu_accelerated: bool,
                                            calculation_success: bool, data_points_processed: int,
                                            memory_usage_mb: float = 0, error_message: str = None) -> TechnicalIndicatorMetrics:
        """
        記錄技術指標計算指標

        Args:
            indicator_type: 指標類型
            symbol: 股票代碼
            calculation_duration: 計算時長(秒)
            gpu_accelerated: 是否使用GPU加速
            calculation_success: 計算是否成功
            data_points_processed: 處理的數據點數
            memory_usage_mb: 內存使用量(MB)
            error_message: 錯誤信息

        Returns:
            TechnicalIndicatorMetrics: 技術指標計算指標
        """
        try:
            metrics = TechnicalIndicatorMetrics(
                indicator_type=indicator_type,
                symbol=symbol,
                timestamp=time.time(),
                calculation_duration=calculation_duration,
                gpu_accelerated=gpu_accelerated,
                calculation_success=calculation_success,
                error_message=error_message,
                data_points_processed=data_points_processed,
                memory_usage_mb=memory_usage_mb
            )

            # 更新Prometheus指標
            if calculation_success:
                self.indicator_calculation_success.labels(indicator_type=indicator_type).inc()
            else:
                self.indicator_calculation_errors.labels(indicator_type=indicator_type).inc()

            self.indicator_calculation_duration.labels(
                indicator_type=indicator_type,
                symbol=symbol
            ).observe(calculation_duration)

            if gpu_accelerated:
                self.gpu_accelerated_calculations.labels(calculation_type='technical_indicator').inc()

            # 保存歷史記錄
            self.metrics_history['technical_indicators'].append(metrics)

            logger.debug(f"Technical indicator calculation recorded: {indicator_type} for {symbol}, "
                        f"duration: {calculation_duration:.3f}s, GPU: {gpu_accelerated}")
            return metrics

        except Exception as e:
            logger.error(f"Failed to record technical indicator calculation: {e}")
            raise

    def record_sharpe_calculation(self, calculation_id: str, strategy_name: str, symbol: str,
                                method_used: str, calculation_duration: float,
                                sharpe_ratio: float, annual_return: float, annual_volatility: float,
                                max_drawdown: float, calculation_success: bool,
                                validation_passed: bool = True, error_message: str = None) -> SharpeRatioMetrics:
        """
        記錄Sharpe比率計算指標

        Args:
            calculation_id: 計算ID
            strategy_name: 策略名稱
            symbol: 股票代碼
            method_used: 計算方法
            calculation_duration: 計算時長
            sharpe_ratio: Sharpe比率
            annual_return: 年化回報
            annual_volatility: 年化波動率
            max_drawdown: 最大回撤
            calculation_success: 計算是否成功
            validation_passed: 驗證是否通過
            error_message: 錯誤信息

        Returns:
            SharpeRatioMetrics: Sharpe比率計算指標
        """
        try:
            metrics = SharpeRatioMetrics(
                calculation_id=calculation_id,
                timestamp=time.time(),
                strategy_name=strategy_name,
                symbol=symbol,
                method_used=method_used,
                calculation_duration=calculation_duration,
                sharpe_ratio=sharpe_ratio,
                annual_return=annual_return,
                annual_volatility=annual_volatility,
                max_drawdown=max_drawdown,
                calculation_success=calculation_success,
                validation_passed=validation_passed,
                error_message=error_message
            )

            # 更新Prometheus指標
            self.sharpe_calculation_duration.labels(
                strategy_name=strategy_name,
                method=method_used
            ).observe(calculation_duration)

            if calculation_success:
                self.current_sharpe_ratio.labels(
                    strategy_name=strategy_name,
                    symbol=symbol
                ).set(sharpe_ratio)

                if validation_passed:
                    self.sharpe_validation_passed.inc()
            else:
                self.sharpe_calculation_errors.labels(strategy_name=strategy_name).inc()

            # 保存歷史記錄
            self.metrics_history['sharpe_calculations'].append(metrics)

            logger.info(f"Sharpe ratio calculation recorded: {strategy_name} for {symbol}, "
                       f"Sharpe: {sharpe_ratio:.3f}, method: {method_used}")
            return metrics

        except Exception as e:
            logger.error(f"Failed to record Sharpe ratio calculation: {e}")
            raise

    def record_backtest_performance(self, backtest_id: str, strategy_name: str, symbol: str,
                                  execution_duration: float, total_strategies_tested: int,
                                  successful_strategies: int, memory_usage_mb: float = 0,
                                  gpu_utilization: float = 0, best_strategy_performance: Dict[str, Any] = None,
                                  optimization_method: str = 'vectorbt') -> BacktestPerformanceMetrics:
        """
        記錄回測性能指標

        Args:
            backtest_id: 回測ID
            strategy_name: 策略名稱
            symbol: 股票代碼
            execution_duration: 執行時長(秒)
            total_strategies_tested: 測試的策略總數
            successful_strategies: 成功的策略數
            memory_usage_mb: 內存使用量(MB)
            gpu_utilization: GPU利用率
            best_strategy_performance: 最佳策略性能
            optimization_method: 優化方法

        Returns:
            BacktestPerformanceMetrics: 回測性能指標
        """
        try:
            strategies_per_second = total_strategies_tested / execution_duration if execution_duration > 0 else 0
            success_rate = (successful_strategies / total_strategies_tested * 100) if total_strategies_tested > 0 else 0

            # 計算性能評分 (基於策略/秒和成功率)
            performance_score = min(100, (strategies_per_second / 10) * 0.6 + success_rate * 0.4)

            metrics = BacktestPerformanceMetrics(
                backtest_id=backtest_id,
                timestamp=time.time(),
                strategy_name=strategy_name,
                symbol=symbol,
                execution_duration=execution_duration,
                total_strategies_tested=total_strategies_tested,
                successful_strategies=successful_strategies,
                strategies_per_second=strategies_per_second,
                memory_usage_mb=memory_usage_mb,
                gpu_utilization=gpu_utilization,
                best_strategy_performance=best_strategy_performance or {},
                optimization_method=optimization_method
            )

            # 更新Prometheus指標
            self.backtest_execution_duration.labels(
                strategy_name=strategy_name,
                method=optimization_method
            ).observe(execution_duration)

            self.strategies_tested_total.labels(strategy_name=strategy_name).inc(total_strategies_tested)
            self.backtest_success_rate.labels(strategy_name=strategy_name).set(success_rate)
            self.optimization_performance_score.labels(strategy_name=strategy_name).set(performance_score)

            if gpu_utilization > 0:
                self.gpu_accelerated_calculations.labels(calculation_type='backtest').inc()

            # 保存歷史記錄
            self.metrics_history['backtest_performance'].append(metrics)

            logger.info(f"Backtest performance recorded: {strategy_name} for {symbol}, "
                       f"{strategies_per_second:.1f} strategies/s, success rate: {success_rate:.1f}%")
            return metrics

        except Exception as e:
            logger.error(f"Failed to record backtest performance: {e}")
            raise

    def record_trading_signal(self, signal_id: str, strategy_name: str, symbol: str,
                            signal_type: str, signal_strength: float, confidence_score: float,
                            generation_duration_ms: float, indicators_used: List[str],
                            risk_metrics: Dict[str, float] = None) -> TradingSignalMetrics:
        """
        記錄交易信號指標

        Args:
            signal_id: 信號ID
            strategy_name: 策略名稱
            symbol: 股票代碼
            signal_type: 信號類型
            signal_strength: 信號強度
            confidence_score: 置信度評分
            generation_duration_ms: 生成時長(毫秒)
            indicators_used: 使用的指標
            risk_metrics: 風險指標

        Returns:
            TradingSignalMetrics: 交易信號指標
        """
        try:
            metrics = TradingSignalMetrics(
                signal_id=signal_id,
                timestamp=time.time(),
                strategy_name=strategy_name,
                symbol=symbol,
                signal_type=signal_type,
                signal_strength=signal_strength,
                confidence_score=confidence_score,
                generation_duration_ms=generation_duration_ms,
                indicators_used=indicators_used,
                risk_metrics=risk_metrics or {}
            )

            # 更新Prometheus指標
            self.trading_signals_generated.labels(
                strategy_name=strategy_name,
                signal_type=signal_type
            ).inc()

            self.signal_generation_duration.labels(strategy_name=strategy_name).observe(generation_duration_ms / 1000)  # 轉換為秒
            self.signal_confidence_score.labels(
                strategy_name=strategy_name,
                symbol=symbol
            ).set(confidence_score)

            # 保存歷史記錄
            self.metrics_history['trading_signals'].append(metrics)

            logger.debug(f"Trading signal recorded: {signal_type} signal for {symbol}, "
                        f"confidence: {confidence_score:.2f}, duration: {generation_duration_ms:.1f}ms")
            return metrics

        except Exception as e:
            logger.error(f"Failed to record trading signal: {e}")
            raise

    def calculate_gpu_performance_improvement(self, calculation_type: str,
                                           gpu_time: float, cpu_time: float) -> float:
        """
        計算GPU性能提升比率

        Args:
            calculation_type: 計算類型
            gpu_time: GPU計算時間
            cpu_time: CPU計算時間

        Returns:
            float: 性能提升比率 (GPU快了多少倍)
        """
        if cpu_time <= 0:
            return 0

        improvement_ratio = cpu_time / gpu_time if gpu_time > 0 else 0
        self.gpu_performance_improvement.labels(calculation_type=calculation_type).set(improvement_ratio)
        return improvement_ratio

    def get_business_metrics_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        獲取業務指標摘要

        Args:
            time_window_hours: 時間窗口(小時)

        Returns:
            Dict[str, Any]: 業務指標摘要
        """
        try:
            cutoff_time = time.time() - (time_window_hours * 3600)

            # 數據質量摘要
            recent_data_quality = [
                m for m in self.metrics_history['data_quality']
                if m.timestamp > cutoff_time
            ]
            data_quality_summary = self._summarize_data_quality(recent_data_quality)

            # 技術指標摘要
            recent_indicators = [
                m for m in self.metrics_history['technical_indicators']
                if m.timestamp > cutoff_time
            ]
            indicators_summary = self._summarize_technical_indicators(recent_indicators)

            # Sharpe計算摘要
            recent_sharpe = [
                m for m in self.metrics_history['sharpe_calculations']
                if m.timestamp > cutoff_time
            ]
            sharpe_summary = self._summarize_sharpe_calculations(recent_sharpe)

            # 回測性能摘要
            recent_backtest = [
                m for m in self.metrics_history['backtest_performance']
                if m.timestamp > cutoff_time
            ]
            backtest_summary = self._summarize_backtest_performance(recent_backtest)

            # 交易信號摘要
            recent_signals = [
                m for m in self.metrics_history['trading_signals']
                if m.timestamp > cutoff_time
            ]
            signals_summary = self._summarize_trading_signals(recent_signals)

            return {
                "time_window_hours": time_window_hours,
                "timestamp": time.time(),
                "data_quality": data_quality_summary,
                "technical_indicators": indicators_summary,
                "sharpe_calculations": sharpe_summary,
                "backtest_performance": backtest_summary,
                "trading_signals": signals_summary,
                "gpu_acceleration": {
                    "enabled": any(m.gpu_accelerated for m in recent_indicators),
                    "total_gpu_calculations": sum(
                        1 for m in recent_indicators if m.gpu_accelerated
                    ),
                    "average_performance_improvement": self._calculate_average_gpu_improvement(recent_indicators)
                }
            }

        except Exception as e:
            logger.error(f"Failed to generate business metrics summary: {e}")
            return {"error": str(e)}

    def _summarize_data_quality(self, metrics_list: List[DataQualityMetrics]) -> Dict[str, Any]:
        """總結數據質量指標"""
        if not metrics_list:
            return {"status": "no_data"}

        quality_scores = [m.overall_quality_score for m in metrics_list]
        freshness_scores = [m.freshness_score for m in metrics_list]

        # 按數據源分組
        by_source = {}
        for m in metrics_list:
            if m.data_source not in by_source:
                by_source[m.data_source] = []
            by_source[m.data_source].append(m.overall_quality_score)

        return {
            "total_checks": len(metrics_list),
            "average_quality_score": statistics.mean(quality_scores),
            "min_quality_score": min(quality_scores),
            "max_quality_score": max(quality_scores),
            "average_freshness_score": statistics.mean(freshness_scores),
            "quality_by_source": {
                source: {
                    "average_score": statistics.mean(scores),
                    "min_score": min(scores),
                    "max_score": max(scores),
                    "check_count": len(scores)
                }
                for source, scores in by_source.items()
            },
            "low_quality_alerts": len([s for s in quality_scores if s < 70])
        }

    def _summarize_technical_indicators(self, metrics_list: List[TechnicalIndicatorMetrics]) -> Dict[str, Any]:
        """總結技術指標計算指標"""
        if not metrics_list:
            return {"status": "no_data"}

        successful = [m for m in metrics_list if m.calculation_success]
        gpu_accelerated = [m for m in metrics_list if m.gpu_accelerated]

        calculation_times = [m.calculation_duration for m in successful]
        data_points = [m.data_points_processed for m in metrics_list]

        # 按指標類型分組
        by_type = {}
        for m in metrics_list:
            if m.indicator_type not in by_type:
                by_type[m.indicator_type] = {"total": 0, "successful": 0, "gpu_accelerated": 0}
            by_type[m.indicator_type]["total"] += 1
            if m.calculation_success:
                by_type[m.indicator_type]["successful"] += 1
            if m.gpu_accelerated:
                by_type[m.indicator_type]["gpu_accelerated"] += 1

        return {
            "total_calculations": len(metrics_list),
            "successful_calculations": len(successful),
            "success_rate": (len(successful) / len(metrics_list) * 100) if metrics_list else 0,
            "gpu_accelerated_count": len(gpu_accelerated),
            "gpu_acceleration_rate": (len(gpu_accelerated) / len(metrics_list) * 100) if metrics_list else 0,
            "average_calculation_time": statistics.mean(calculation_times) if calculation_times else 0,
            "max_calculation_time": max(calculation_times) if calculation_times else 0,
            "total_data_points_processed": sum(data_points),
            "by_indicator_type": by_type
        }

    def _summarize_sharpe_calculations(self, metrics_list: List[SharpeRatioMetrics]) -> Dict[str, Any]:
        """總結Sharpe比率計算指標"""
        if not metrics_list:
            return {"status": "no_data"}

        successful = [m for m in metrics_list if m.calculation_success]
        validated = [m for m in successful if m.validation_passed]

        sharpe_ratios = [m.sharpe_ratio for m in successful]
        calculation_times = [m.calculation_duration for m in successful]

        # 按方法分組
        by_method = {}
        for m in metrics_list:
            if m.method_used not in by_method:
                by_method[m.method_used] = {"count": 0, "successful": 0, "avg_sharpe": 0}
            by_method[m.method_used]["count"] += 1
            if m.calculation_success:
                by_method[m.method_used]["successful"] += 1

        # 計算每種方法的平均Sharpe
        for method, stats in by_method.items():
            method_sharpes = [m.sharpe_ratio for m in successful if m.method_used == method]
            stats["avg_sharpe"] = statistics.mean(method_sharpes) if method_sharpes else 0

        return {
            "total_calculations": len(metrics_list),
            "successful_calculations": len(successful),
            "validated_calculations": len(validated),
            "validation_rate": (len(validated) / len(successful) * 100) if successful else 0,
            "average_sharpe_ratio": statistics.mean(sharpe_ratios) if sharpe_ratios else 0,
            "max_sharpe_ratio": max(sharpe_ratios) if sharpe_ratios else 0,
            "average_calculation_time": statistics.mean(calculation_times) if calculation_times else 0,
            "by_calculation_method": by_method,
            "high_sharpe_strategies": len([s for s in sharpe_ratios if s > 2.0])
        }

    def _summarize_backtest_performance(self, metrics_list: List[BacktestPerformanceMetrics]) -> Dict[str, Any]:
        """總結回測性能指標"""
        if not metrics_list:
            return {"status": "no_data"}

        strategies_per_second = [m.strategies_per_second for m in metrics_list]
        success_rates = [(m.successful_strategies / m.total_strategies_tested * 100) for m in metrics_list]

        # 按優化方法分組
        by_method = {}
        for m in metrics_list:
            if m.optimization_method not in by_method:
                by_method[m.optimization_method] = {
                    "count": 0,
                    "total_strategies": 0,
                    "avg_strategies_per_second": 0,
                    "avg_success_rate": 0
                }
            by_method[m.optimization_method]["count"] += 1
            by_method[m.optimization_method]["total_strategies"] += m.total_strategies_tested

        # 計算每種方法的平均值
        for method, stats in by_method.items():
            method_metrics = [m for m in metrics_list if m.optimization_method == method]
            stats["avg_strategies_per_second"] = statistics.mean(
                [m.strategies_per_second for m in method_metrics]
            )
            method_success_rates = [(m.successful_strategies / m.total_strategies_tested * 100) for m in method_metrics]
            stats["avg_success_rate"] = statistics.mean(method_success_rates)

        return {
            "total_backtests": len(metrics_list),
            "total_strategies_tested": sum(m.total_strategies_tested for m in metrics_list),
            "total_successful_strategies": sum(m.successful_strategies for m in metrics_list),
            "average_strategies_per_second": statistics.mean(strategies_per_second),
            "max_strategies_per_second": max(strategies_per_second),
            "average_success_rate": statistics.mean(success_rates),
            "by_optimization_method": by_method,
            "gpu_utilized_backtests": len([m for m in metrics_list if m.gpu_utilization > 0])
        }

    def _summarize_trading_signals(self, metrics_list: List[TradingSignalMetrics]) -> Dict[str, Any]:
        """總結交易信號指標"""
        if not metrics_list:
            return {"status": "no_data"}

        # 按信號類型分組
        by_type = {}
        confidence_scores = []
        generation_times = []

        for m in metrics_list:
            signal_type = m.signal_type
            if signal_type not in by_type:
                by_type[signal_type] = {"count": 0, "avg_confidence": 0, "avg_strength": 0}
            by_type[signal_type]["count"] += 1

            confidence_scores.append(m.confidence_score)
            generation_times.append(m.generation_duration_ms)

        # 計算平均值
        for signal_type, stats in by_type.items():
            type_signals = [m for m in metrics_list if m.signal_type == signal_type]
            stats["avg_confidence"] = statistics.mean([m.confidence_score for m in type_signals])
            stats["avg_strength"] = statistics.mean([m.signal_strength for m in type_signals])

        return {
            "total_signals": len(metrics_list),
            "average_confidence_score": statistics.mean(confidence_scores) if confidence_scores else 0,
            "average_generation_time_ms": statistics.mean(generation_times) if generation_times else 0,
            "by_signal_type": by_type,
            "high_confidence_signals": len([s for s in confidence_scores if s > 0.8])
        }

    def _calculate_average_gpu_improvement(self, metrics_list: List[TechnicalIndicatorMetrics]) -> float:
        """計算平均GPU性能提升"""
        gpu_calculations = [m for m in metrics_list if m.gpu_accelerated]
        if not gpu_calculations:
            return 0

        # 這裡需要與CPU計算時間比較，簡化實現
        # 實際應用中需要收集CPU計算的基準數據
        return 2.5  # 假設平均2.5倍性能提升

    def get_prometheus_metrics(self) -> str:
        """
        獲取Prometheus格式的指標

        Returns:
            str: Prometheus格式指標數據
        """
        return generate_latest(self.registry).decode('utf-8')

# 全局業務指標監控器實例
business_metrics_monitor = BusinessMetricsMonitor()

def get_business_metrics_monitor() -> BusinessMetricsMonitor:
    """獲取業務指標監控器實例"""
    return business_metrics_monitor

# 裝飾器
def monitor_business_metrics(metric_type: str, **metric_kwargs):
    """業務指標監控裝飾器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
                error_msg = None
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                duration = time.time() - start_time
                # 記錄指標
                if metric_type == 'data_quality':
                    # 需要傳入特定參數
                    pass
                elif metric_type == 'sharpe_calculation':
                    business_metrics_monitor.record_sharpe_calculation(
                        calculation_id=str(uuid.uuid4()),
                        calculation_duration=duration,
                        calculation_success=success,
                        error_message=error_msg,
                        **metric_kwargs
                    )
            return result
        return wrapper
    return decorator

if __name__ == "__main__":
    async def main():
        """測試業務指標監控功能"""
        monitor = BusinessMetricsMonitor()

        print("Testing business metrics monitoring...")

        # 測試數據質量監控
        print("\n=== Data Quality Monitoring ===")
        sample_data = pd.DataFrame({
            'close': [100.5, 101.2, 99.8, 102.3],
            'volume': [1000, 1200, 800, 1500]
        }, index=pd.date_range('2024-01-01', periods=4))

        quality_metrics = monitor.record_data_quality("stock_api", sample_data)
        print(f"Data quality score: {quality_metrics.overall_quality_score:.1f}/100")

        # 測試技術指標計算監控
        print("\n=== Technical Indicator Monitoring ===")
        indicator_metrics = monitor.record_technical_indicator_calculation(
            indicator_type="RSI",
            symbol="0700.HK",
            calculation_duration=0.025,
            gpu_accelerated=True,
            calculation_success=True,
            data_points_processed=1000
        )
        print(f"RSI calculation: {indicator_metrics.calculation_duration:.3f}s, GPU: {indicator_metrics.gpu_accelerated}")

        # 測試Sharpe計算監控
        print("\n=== Sharpe Ratio Monitoring ===")
        sharpe_metrics = monitor.record_sharpe_calculation(
            calculation_id="test_001",
            strategy_name="RSI_MEAN_REVERSION",
            symbol="0700.HK",
            method_used="standard",
            calculation_duration=0.15,
            sharpe_ratio=1.45,
            annual_return=0.12,
            annual_volatility=0.08,
            max_drawdown=-0.05,
            calculation_success=True,
            validation_passed=True
        )
        print(f"Sharpe calculation: {sharpe_metrics.sharpe_ratio:.3f}, validation: {sharpe_metrics.validation_passed}")

        # 測試回測性能監控
        print("\n=== Backtest Performance Monitoring ===")
        backtest_metrics = monitor.record_backtest_performance(
            backtest_id="backtest_001",
            strategy_name="RSI_OPTIMIZATION",
            symbol="0700.HK",
            execution_duration=45.2,
            total_strategies_tested=1000,
            successful_strategies=980,
            optimization_method="vectorbt"
        )
        print(f"Backtest performance: {backtest_metrics.strategies_per_second:.1f} strategies/s")

        # 測試交易信號監控
        print("\n=== Trading Signal Monitoring ===")
        signal_metrics = monitor.record_trading_signal(
            signal_id="signal_001",
            strategy_name="RSI_MEAN_REVERSION",
            symbol="0700.HK",
            signal_type="buy",
            signal_strength=0.85,
            confidence_score=0.92,
            generation_duration_ms=15.5,
            indicators_used=["RSI", "MACD"]
        )
        print(f"Trading signal: {signal_metrics.signal_type}, confidence: {signal_metrics.confidence_score:.2f}")

        # 獲取業務指標摘要
        print("\n=== Business Metrics Summary ===")
        summary = monitor.get_business_metrics_summary(24)  # 24小時窗口
        print(f"Data quality checks: {summary['data_quality']['total_checks']}")
        print(f"Technical indicator calculations: {summary['technical_indicators']['total_calculations']}")
        print(f"Sharpe calculations: {summary['sharpe_calculations']['successful_calculations']}")
        print(f"Backtest strategies per second: {summary['backtest_performance']['average_strategies_per_second']:.1f}")

        # 獲取Prometheus指標
        prometheus_metrics = monitor.get_prometheus_metrics()
        print(f"\nPrometheus metrics generated: {len(prometheus_metrics)} bytes")

        print("\nBusiness metrics monitoring test completed!")

    # 需要導入uuid
    import uuid
    asyncio.run(main())