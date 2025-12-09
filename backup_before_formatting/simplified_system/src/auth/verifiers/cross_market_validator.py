#!/usr/bin/env python3
"""
Cross-Market Validator - Task 14
跨市场验证器 - 任务14

Cross-market validation including correlations, arbitrage opportunities, and exchange rates
跨市场验证，包括相关性、套利机会和汇率分析

This module implements:
- Cross-market correlation analysis
- Arbitrage opportunity detection
- Exchange rate consistency validation
- Market efficiency testing
- Cross-asset relationship validation
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import pearsonr, spearmanr

# Import authentication interfaces
from .interfaces.verifier_interface import IVerifier
from .interfaces.auth_result import AuthResult, Verdict
from .content_validation_layer import ValidationSeverity, AnomalyType, AnomalyDetection, ValidationResult

# Setup logging
logger = logging.getLogger(__name__)


class ValidationType(str, Enum):
    """验证类型"""
    CORRELATION = "correlation"
    ARBITRAGE = "arbitrage"
    EXCHANGE_RATE = "exchange_rate"
    MARKET_EFFICIENCY = "market_efficiency"
    CROSS_ASSET = "cross_asset"


@dataclass
class MarketData:
    """市场数据结构"""
    market_name: str
    data: pd.DataFrame
    data_type: str  # 'stock', 'forex', 'commodity', 'bond'
    currency: str
    timestamp_col: str = 'timestamp'


@dataclass
class ValidationResult:
    """验证结果"""
    validation_type: ValidationType
    market_pair: Tuple[str, str]
    passed: bool
    confidence: float
    execution_time_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    anomalies: List[AnomalyDetection] = field(default_factory=list)
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class CrossMarketValidator(IVerifier):
    """跨市场验证器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("CrossMarketValidator", config)
        self.supported_data_types = ["stock_data", "forex_data", "commodity_data", "bond_data"]

        # 配置参数
        self.correlation_threshold = self.config.get('correlation_threshold', 0.7)
        self.arbitrage_threshold = self.config.get('arbitrage_threshold', 0.01)  # 1%
        self.exchange_rate_tolerance = self.config.get('exchange_rate_tolerance', 0.02)  # 2%
        self.min_data_points = self.config.get('min_data_points', 50)
        self.price_column = self.config.get('price_column', 'close')

        # 香港市场特定配置
        self.hk_main_indices = ['HSI', 'HSCEI', 'HSTECH']
        self.major_currencies = ['USD', 'EUR', 'JPY', 'CNY', 'GBP']
        self.hk_trading_hours = {
            'start': '09:30',
            'end': '16:00',
            'timezone': 'Asia/Hong_Kong'
        }

    def get_verifier_type(self) -> str:
        return "cross_market"

    def get_supported_data_types(self) -> List[str]:
        return self.supported_data_types

    async def verify(self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None) -> AuthResult:
        """执行跨市场验证"""
        start_time = time.time()

        try:
            # 解析输入数据
            market_data_list = self._parse_market_data(data, context)

            if len(market_data_list) < 2:
                return AuthResult(
                    data_id=data_id,
                    data_type=context.get('data_type', 'unknown') if context else 'unknown',
                    data_source=context.get('data_source', 'unknown') if context else 'unknown',
                    overall_verdict=Verdict.UNKNOWN,
                    overall_confidence=0.5,
                    status="completed",
                    total_execution_time_ms=(time.time() - start_time) * 1000,
                    metadata={
                        'message': 'Insufficient market data for cross-market validation. Minimum 2 markets required.',
                        'markets_provided': len(market_data_list)
                    }
                )

            # 执行所有类型的跨市场验证
            validation_results = []

            # 1. 相关性分析
            correlation_results = await self._validate_correlations(market_data_list)
            validation_results.extend(correlation_results)

            # 2. 套利机会检测
            arbitrage_results = await self._detect_arbitrage_opportunities(market_data_list)
            validation_results.extend(arbitrage_results)

            # 3. 汇率一致性验证
            exchange_rate_results = await self._validate_exchange_rates(market_data_list)
            validation_results.extend(exchange_rate_results)

            # 4. 市场效率测试
            efficiency_results = await self._test_market_efficiency(market_data_list)
            validation_results.extend(efficiency_results)

            # 5. 跨资产关系验证
            cross_asset_results = await self._validate_cross_asset_relationships(market_data_list)
            validation_results.extend(cross_asset_results)

            # 计算综合结果
            passed_validations = sum(1 for r in validation_results if r.passed)
            total_validations = len(validation_results)
            confidence = passed_validations / total_validations if total_validations > 0 else 0.0

            # 收集所有异常
            all_anomalies = []
            for result in validation_results:
                all_anomalies.extend(result.anomalies)

            # 确定最终结论
            if confidence >= 0.8 and len(all_anomalies) == 0:
                verdict = Verdict.AUTHENTIC
            elif confidence >= 0.6 and len(all_anomalies) < 5:
                verdict = Verdict.SUSPICIOUS
            else:
                verdict = Verdict.FALSIFIED

            execution_time = (time.time() - start_time) * 1000

            result = AuthResult(
                data_id=data_id,
                data_type=context.get('data_type', 'unknown') if context else 'unknown',
                data_source=context.get('data_source', 'unknown') if context else 'unknown',
                overall_verdict=verdict,
                overall_confidence=confidence,
                status="completed",
                total_execution_time_ms=execution_time,
                metadata={
                    'validation_results': [r.__dict__ for r in validation_results],
                    'total_validations': total_validations,
                    'passed_validations': passed_validations,
                    'total_anomalies': len(all_anomalies),
                    'markets_analyzed': [m.market_name for m in market_data_list],
                    'validation_types_performed': list(set(r.validation_type.value for r in validation_results))
                }
            )

            logger.info(f"Cross-market validation completed for {data_id}: {verdict.value} "
                       f"(confidence: {confidence:.3f}, anomalies: {len(all_anomalies)})")
            return result

        except Exception as e:
            logger.error(f"Cross-market validation failed for {data_id}: {str(e)}")
            execution_time = (time.time() - start_time) * 1000
            return AuthResult(
                data_id=data_id,
                data_type="unknown",
                data_source="unknown",
                overall_verdict=Verdict.ERROR,
                overall_confidence=0.0,
                status="failed",
                total_execution_time_ms=execution_time,
                error_message=str(e)
            )

    def _parse_market_data(self, data: Any, context: Optional[Dict[str, Any]] = None) -> List[MarketData]:
        """解析市场数据"""
        market_data_list = []

        # 处理单个市场数据
        if isinstance(data, dict):
            if 'data' in data:
                # 单个市场的数据
                df = pd.DataFrame(data['data'])
                market_name = data.get('market_name', 'unknown')
                data_type = data.get('data_type', 'stock')
                currency = data.get('currency', 'HKD')

                market_data = MarketData(
                    market_name=market_name,
                    data=df,
                    data_type=data_type,
                    currency=currency,
                    timestamp_col='timestamp' if 'timestamp' in df.columns else 'date'
                )
                market_data_list.append(market_data)

        # 处理多个市场数据
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'data' in item:
                    df = pd.DataFrame(item['data'])
                    market_name = item.get('market_name', f'market_{len(market_data_list)}')
                    data_type = item.get('data_type', 'stock')
                    currency = item.get('currency', 'HKD')

                    market_data = MarketData(
                        market_name=market_name,
                        data=df,
                        data_type=data_type,
                        currency=currency,
                        timestamp_col='timestamp' if 'timestamp' in df.columns else 'date'
                    )
                    market_data_list.append(market_data)

        # 如果context中提供了市场数据信息，使用它们
        elif context and 'market_data' in context:
            for market_info in context['market_data']:
                if 'data' in market_info:
                    df = pd.DataFrame(market_info['data'])
                    market_name = market_info.get('name', 'unknown')
                    data_type = market_info.get('type', 'stock')
                    currency = market_info.get('currency', 'HKD')

                    market_data = MarketData(
                        market_name=market_name,
                        data=df,
                        data_type=data_type,
                        currency=currency,
                        timestamp_col='timestamp' if 'timestamp' in df.columns else 'date'
                    )
                    market_data_list.append(market_data)

        return market_data_list

    async def _validate_correlations(self, markets: List[MarketData]) -> List[ValidationResult]:
        """验证市场相关性"""
        results = []

        # 只对相同类型的资产进行相关性分析
        stock_markets = [m for m in markets if m.data_type == 'stock']
        forex_markets = [m for m in markets if m.data_type == 'forex']
        commodity_markets = [m for m in markets if m.data_type == 'commodity']

        # 股票市场相关性分析
        if len(stock_markets) >= 2:
            stock_correlations = await self._analyze_market_correlations(stock_markets)
            results.extend(stock_correlations)

        # 外汇市场相关性分析
        if len(forex_markets) >= 2:
            forex_correlations = await self._analyze_market_correlations(forex_markets)
            results.extend(forex_correlations)

        # 商品市场相关性分析
        if len(commodity_markets) >= 2:
            commodity_correlations = await self._analyze_market_correlations(commodity_markets)
            results.extend(commodity_correlations)

        return results

    async def _analyze_market_correlations(self, markets: List[MarketData]) -> List[ValidationResult]:
        """分析市场间的相关性"""
        results = []

        for i, market1 in enumerate(markets):
            for j, market2 in enumerate(markets[i+1:], i+1):
                start_time = time.time()

                try:
                    # 准备价格数据
                    prices1 = self._prepare_price_data(market1)
                    prices2 = self._prepare_price_data(market2)

                    # 对齐时间序列
                    aligned_prices1, aligned_prices2 = self._align_time_series(prices1, prices2)

                    if len(aligned_prices1) < self.min_data_points:
                        results.append(ValidationResult(
                            validation_type=ValidationType.CORRELATION,
                            market_pair=(market1.market_name, market2.market_name),
                            passed=False,
                            confidence=0.0,
                            execution_time_ms=(time.time() - start_time) * 1000,
                            details={'message': f'Insufficient aligned data points: {len(aligned_prices1)} < {self.min_data_points}'}
                        ))
                        continue

                    # 计算相关性
                    pearson_corr, pearson_pvalue = pearsonr(aligned_prices1, aligned_prices2)
                    spearman_corr, spearman_pvalue = spearmanr(aligned_prices1, aligned_prices2)

                    # 检查相关性是否合理
                    anomalies = []

                    # 异常1: 相关性突然变化（如果有历史数据）
                    if len(aligned_prices1) > 100:
                        window_size = min(30, len(aligned_prices1) // 4)
                        rolling_corrs = []
                        for k in range(len(aligned_prices1) - window_size + 1):
                            window_corr, _ = pearsonr(
                                aligned_prices1[k:k+window_size],
                                aligned_prices2[k:k+window_size]
                            )
                            rolling_corrs.append(window_corr)

                        if rolling_corrs:
                            recent_corr = rolling_corrs[-1]
                            historical_avg = np.mean(rolling_corrs[:-1])
                            if abs(recent_corr - historical_avg) > 0.3:
                                anomalies.append(AnomalyDetection(
                                    anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                                    timestamp=aligned_prices1.index[-1],
                                    field_name='correlation_shift',
                                    value=recent_corr,
                                    severity=ValidationSeverity.MEDIUM,
                                    confidence=0.7,
                                    context={
                                        'recent_correlation': recent_corr,
                                        'historical_average': historical_avg,
                                        'shift_magnitude': abs(recent_corr - historical_avg)
                                    }
                                ))

                    # 验证相关性是否在合理范围内
                    # 对于同类型市场，相关性通常应该为正
                    expected_correlation_sign = 1 if market1.data_type == market2.data_type else 0
                    actual_correlation = pearson_corr

                    passed = True
                    if expected_correlation_sign == 1 and actual_correlation < -0.3:
                        # 同类型市场出现强负相关，可能是异常
                        passed = False
                        anomalies.append(AnomalyDetection(
                            anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                            timestamp=aligned_prices1.index[-1],
                            field_name='unexpected_negative_correlation',
                            value=actual_correlation,
                            severity=ValidationSeverity.HIGH,
                            confidence=0.8,
                            context={
                                'expected_positive': True,
                                'actual_correlation': actual_correlation,
                                'market1_type': market1.data_type,
                                'market2_type': market2.data_type
                            }
                        ))

                    confidence = 1.0 if passed else max(0.3, 1.0 - abs(actual_correlation - expected_correlation_sign))

                    execution_time = (time.time() - start_time) * 1000

                    result = ValidationResult(
                        validation_type=ValidationType.CORRELATION,
                        market_pair=(market1.market_name, market2.market_name),
                        passed=passed,
                        confidence=confidence,
                        execution_time_ms=execution_time,
                        details={
                            'pearson_correlation': pearson_corr,
                            'pearson_pvalue': pearson_pvalue,
                            'spearman_correlation': spearman_corr,
                            'spearman_pvalue': spearman_pvalue,
                            'data_points': len(aligned_prices1),
                            'market1_type': market1.data_type,
                            'market2_type': market2.data_type
                        },
                        anomalies=anomalies
                    )
                    results.append(result)

                except Exception as e:
                    results.append(ValidationResult(
                        validation_type=ValidationType.CORRELATION,
                        market_pair=(market1.market_name, market2.market_name),
                        passed=False,
                        confidence=0.0,
                        execution_time_ms=(time.time() - start_time) * 1000,
                        error_message=str(e)
                    ))

        return results

    async def _detect_arbitrage_opportunities(self, markets: List[MarketData]) -> List[ValidationResult]:
        """检测套利机会"""
        results = []

        # 识别同一资产在不同市场的数据
        asset_groups = {}
        for market in markets:
            # 这里假设market.data中包含资产标识符
            # 实际实现中需要根据具体数据格式调整
            if 'symbol' in market.data.columns:
                symbols = market.data['symbol'].unique()
                for symbol in symbols:
                    if symbol not in asset_groups:
                        asset_groups[symbol] = []
                    asset_groups[symbol].append(market)

        # 对每个资产组进行套利分析
        for symbol, symbol_markets in asset_groups.items():
            if len(symbol_markets) >= 2:
                arbitrage_results = await self._analyze_arbitrage_for_symbol(symbol, symbol_markets)
                results.extend(arbitrage_results)

        return results

    async def _analyze_arbitrage_for_symbol(self, symbol: str, markets: List[MarketData]) -> List[ValidationResult]:
        """分析特定资产的套利机会"""
        results = []

        # 获取各市场的价格数据
        market_prices = {}
        for market in markets:
            symbol_data = market.data[market.data['symbol'] == symbol] if 'symbol' in market.data.columns else market.data
            if len(symbol_data) > 0 and self.price_column in symbol_data.columns:
                market_prices[market.market_name] = {
                    'prices': symbol_data[self.price_column],
                    'timestamps': symbol_data[market.timestamp_col],
                    'currency': market.currency
                }

        if len(market_prices) < 2:
            return results

        # 创建结果
        start_time = time.time()
        market_names = list(market_prices.keys())

        try:
            # 对齐各市场的价格数据
            common_timestamps = None
            aligned_prices = {}

            for market_name, price_info in market_prices.items():
                timestamps = pd.to_datetime(price_info['timestamps'])
                if common_timestamps is None:
                    common_timestamps = set(timestamps)
                else:
                    common_timestamps &= set(timestamps)

            common_timestamps = sorted(common_timestamps)

            if len(common_timestamps) < 10:
                results.append(ValidationResult(
                    validation_type=ValidationType.ARBITRAGE,
                    market_pair=tuple(market_names),
                    passed=True,  # 缺乏数据不算失败
                    confidence=0.5,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    details={'message': f'Insufficient common timestamps: {len(common_timestamps)}'}
                ))
                return results

            # 对齐价格数据
            for market_name, price_info in market_prices.items():
                df = pd.DataFrame({
                    'timestamp': pd.to_datetime(price_info['timestamps']),
                    'price': price_info['prices']
                })
                df = df.set_index('timestamp').loc[common_timestamps]
                aligned_prices[market_name] = df['price']

            # 计算价格差异和套利机会
            arbitrage_opportunities = []
            price_diffs = []

            for i in range(1, len(common_timestamps)):
                timestamp = common_timestamps[i]
                prices_at_timestamp = {name: aligned_prices[name].iloc[i] for name in market_names}

                # 找出最高价和最低价
                max_price = max(prices_at_timestamp.values())
                min_price = min(prices_at_timestamp.values())

                # 计算价格差异百分比
                price_diff_pct = (max_price - min_price) / min_price if min_price > 0 else 0
                price_diffs.append(price_diff_pct)

                # 检查是否存在套利机会
                if price_diff_pct > self.arbitrage_threshold:
                    max_market = max(prices_at_timestamp, key=prices_at_timestamp.get)
                    min_market = min(prices_at_timestamp, key=prices_at_timestamp.get)

                    arbitrage_opportunities.append({
                        'timestamp': timestamp,
                        'price_difference_pct': price_diff_pct,
                        'max_price_market': max_market,
                        'min_price_market': min_market,
                        'max_price': prices_at_timestamp[max_market],
                        'min_price': prices_at_timestamp[min_market]
                    })

            # 创建异常检测结果
            anomalies = []
            for opportunity in arbitrage_opportunities:
                anomaly = AnomalyDetection(
                    anomaly_type=AnomalyType.PRICE_JUMP,
                    timestamp=opportunity['timestamp'],
                    field_name='arbitrage_opportunity',
                    value=opportunity['price_difference_pct'],
                    severity=ValidationSeverity.HIGH if opportunity['price_difference_pct'] > self.arbitrage_threshold * 2 else ValidationSeverity.MEDIUM,
                    confidence=0.9,
                    context={
                        'max_price_market': opportunity['max_price_market'],
                        'min_price_market': opportunity['min_price_market'],
                        'max_price': opportunity['max_price'],
                        'min_price': opportunity['min_price'],
                        'arbitrage_threshold': self.arbitrage_threshold
                    }
                )
                anomalies.append(anomaly)

            # 计算统计信息
            avg_price_diff = np.mean(price_diffs) if price_diffs else 0
            max_price_diff = np.max(price_diffs) if price_diffs else 0
            arbitrage_frequency = len(arbitrage_opportunities) / len(price_diffs) if price_diffs else 0

            passed = arbitrage_frequency < 0.05  # 套利机会频率低于5%认为正常
            confidence = 1.0 - arbitrage_frequency

            execution_time = (time.time() - start_time) * 1000

            result = ValidationResult(
                validation_type=ValidationType.ARBITRAGE,
                market_pair=tuple(market_names),
                passed=passed,
                confidence=confidence,
                execution_time_ms=execution_time,
                details={
                    'symbol': symbol,
                    'total_timestamps': len(common_timestamps),
                    'arbitrage_opportunities': len(arbitrage_opportunities),
                    'arbitrage_frequency': arbitrage_frequency,
                    'avg_price_difference_pct': avg_price_diff,
                    'max_price_difference_pct': max_price_diff,
                    'arbitrage_threshold': self.arbitrage_threshold
                },
                anomalies=anomalies
            )
            results.append(result)

        except Exception as e:
            results.append(ValidationResult(
                validation_type=ValidationType.ARBITRAGE,
                market_pair=tuple(market_names),
                passed=False,
                confidence=0.0,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            ))

        return results

    async def _validate_exchange_rates(self, markets: List[MarketData]) -> List[ValidationResult]:
        """验证汇率一致性"""
        results = []

        # 收集所有包含汇率信息的市场
        forex_markets = [m for m in markets if m.data_type == 'forex']

        if len(forex_markets) < 2:
            return results

        # 分析汇率对的一致性
        for i, market1 in enumerate(forex_markets):
            for j, market2 in enumerate(forex_markets[i+1:], i+1):
                start_time = time.time()

                try:
                    # 提取汇率数据
                    rates1 = self._extract_exchange_rates(market1)
                    rates2 = self._extract_exchange_rates(market2)

                    if not rates1 or not rates2:
                        continue

                    # 寻找共同的汇率对
                    common_pairs = set(rates1.keys()) & set(rates2.keys())

                    if not common_pairs:
                        continue

                    # 验证每个共同汇率对的一致性
                    anomalies = []
                    validated_pairs = 0
                    consistent_pairs = 0

                    for pair in common_pairs:
                        pair_data1 = rates1[pair]
                        pair_data2 = rates2[pair]

                        # 对齐时间序列
                        aligned_data1, aligned_data2 = self._align_time_series(
                            pair_data1.set_index('timestamp')['rate'],
                            pair_data2.set_index('timestamp')['rate']
                        )

                        if len(aligned_data1) < 10:
                            continue

                        validated_pairs += 1

                        # 计算汇率差异
                        rate_diffs = (aligned_data1 - aligned_data2) / aligned_data2
                        max_diff = rate_diffs.abs().max()
                        avg_diff = rate_diffs.abs().mean()

                        # 检查是否超过容忍度
                        if max_diff > self.exchange_rate_tolerance:
                            # 找到最大差异的时间点
                            max_diff_idx = rate_diffs.abs().idxmax()

                            anomaly = AnomalyDetection(
                                anomaly_type=AnomalyType.PRICE_JUMP,
                                timestamp=max_diff_idx,
                                field_name=f'exchange_rate_inconsistency_{pair}',
                                value=float(max_diff.loc[max_diff_idx]),
                                severity=ValidationSeverity.HIGH if max_diff > self.exchange_rate_tolerance * 2 else ValidationSeverity.MEDIUM,
                                confidence=0.9,
                                context={
                                    'currency_pair': pair,
                                    'market1_rate': float(aligned_data1.loc[max_diff_idx]),
                                    'market2_rate': float(aligned_data2.loc[max_diff_idx]),
                                    'difference_percentage': float(max_diff.loc[max_diff_idx]),
                                    'tolerance': self.exchange_rate_tolerance,
                                    'market1': market1.market_name,
                                    'market2': market2.market_name
                                }
                            )
                            anomalies.append(anomaly)
                        else:
                            consistent_pairs += 1

                    passed = consistent_pairs == validated_pairs
                    confidence = consistent_pairs / validated_pairs if validated_pairs > 0 else 1.0

                    execution_time = (time.time() - start_time) * 1000

                    result = ValidationResult(
                        validation_type=ValidationType.EXCHANGE_RATE,
                        market_pair=(market1.market_name, market2.market_name),
                        passed=passed,
                        confidence=confidence,
                        execution_time_ms=execution_time,
                        details={
                            'common_currency_pairs': list(common_pairs),
                            'validated_pairs': validated_pairs,
                            'consistent_pairs': consistent_pairs,
                            'exchange_rate_tolerance': self.exchange_rate_tolerance
                        },
                        anomalies=anomalies
                    )
                    results.append(result)

                except Exception as e:
                    results.append(ValidationResult(
                        validation_type=ValidationType.EXCHANGE_RATE,
                        market_pair=(market1.market_name, market2.market_name),
                        passed=False,
                        confidence=0.0,
                        execution_time_ms=(time.time() - start_time) * 1000,
                        error_message=str(e)
                    ))

        return results

    async def _test_market_efficiency(self, markets: List[MarketData]) -> List[ValidationResult]:
        """测试市场效率"""
        results = []

        # 只对股票市场进行效率测试
        stock_markets = [m for m in markets if m.data_type == 'stock']

        for market in stock_markets:
            start_time = time.time()

            try:
                # 准备价格数据
                price_data = self._prepare_price_data(market)

                if len(price_data) < self.min_data_points:
                    results.append(ValidationResult(
                        validation_type=ValidationType.MARKET_EFFICIENCY,
                        market_pair=(market.market_name,),
                        passed=False,
                        confidence=0.0,
                        execution_time_ms=(time.time() - start_time) * 1000,
                        details={'message': f'Insufficient data points: {len(price_data)} < {self.min_data_points}'}
                    ))
                    continue

                # 计算收益率
                returns = price_data.pct_change().dropna()

                # 1. 随机游走测试
                # 计算自相关性
                autocorr_lag1 = returns.autocorr(lag=1)
                autocorr_lag5 = returns.autocorr(lag=5)
                autocorr_lag10 = returns.autocorr(lag=10)

                # 2. 方差比检验
                variance_ratio = self._variance_ratio_test(returns)

                # 3. 运行检验（检查价格序列是否为随机游走）
                runs_test_result = self._runs_test(price_data)

                # 判断市场效率
                efficiency_score = 0
                total_tests = 0

                # 自相关性测试
                if abs(autocorr_lag1) < 0.1:
                    efficiency_score += 1
                total_tests += 1

                # 方差比测试（接近1表示随机游走）
                if abs(variance_ratio - 1.0) < 0.2:
                    efficiency_score += 1
                total_tests += 1

                # 运行检验
                if runs_test_result['p_value'] > 0.05:
                    efficiency_score += 1
                total_tests += 1

                efficiency_ratio = efficiency_score / total_tests if total_tests > 0 else 0

                # 识别市场无效率的异常
                anomalies = []
                if efficiency_ratio < 0.5:
                    anomaly = AnomalyDetection(
                        anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                        timestamp=price_data.index[-1],
                        field_name='market_inefficiency',
                        value=efficiency_ratio,
                        severity=ValidationSeverity.MEDIUM,
                        confidence=0.7,
                        context={
                            'efficiency_score': efficiency_score,
                            'total_tests': total_tests,
                            'autocorr_lag1': autocorr_lag1,
                            'variance_ratio': variance_ratio,
                            'runs_p_value': runs_test_result['p_value']
                        }
                    )
                    anomalies.append(anomaly)

                passed = efficiency_ratio >= 0.5
                confidence = efficiency_ratio

                execution_time = (time.time() - start_time) * 1000

                result = ValidationResult(
                    validation_type=ValidationType.MARKET_EFFICIENCY,
                    market_pair=(market.market_name,),
                    passed=passed,
                    confidence=confidence,
                    execution_time_ms=execution_time,
                    details={
                        'efficiency_ratio': efficiency_ratio,
                        'efficiency_score': efficiency_score,
                        'total_tests': total_tests,
                        'autocorrelation_lag1': autocorr_lag1,
                        'autocorrelation_lag5': autocorr_lag5,
                        'autocorrelation_lag10': autocorr_lag10,
                        'variance_ratio': variance_ratio,
                        'runs_test': runs_test_result
                    },
                    anomalies=anomalies
                )
                results.append(result)

            except Exception as e:
                results.append(ValidationResult(
                    validation_type=ValidationType.MARKET_EFFICIENCY,
                    market_pair=(market.market_name,),
                    passed=False,
                    confidence=0.0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error_message=str(e)
                ))

        return results

    async def _validate_cross_asset_relationships(self, markets: List[MarketData]) -> List[ValidationResult]:
        """验证跨资产关系"""
        results = []

        # 按资产类型分组
        asset_groups = {}
        for market in markets:
            if market.data_type not in asset_groups:
                asset_groups[market.data_type] = []
            asset_groups[market.data_type].append(market)

        # 检查传统的跨资产关系
        # 股票 vs 汇率
        if 'stock' in asset_groups and 'forex' in asset_groups:
            stock_forex_results = await self._validate_stock_forex_relationships(
                asset_groups['stock'], asset_groups['forex']
            )
            results.extend(stock_forex_results)

        # 股票 vs 商品
        if 'stock' in asset_groups and 'commodity' in asset_groups:
            stock_commodity_results = await self._validate_stock_commodity_relationships(
                asset_groups['stock'], asset_groups['commodity']
            )
            results.extend(stock_commodity_results)

        return results

    async def _validate_stock_forex_relationships(self, stock_markets: List[MarketData], forex_markets: List[MarketData]) -> List[ValidationResult]:
        """验证股票-外汇关系"""
        results = []

        # 香港股票与美元汇率的关系（港币盯住美元，所以主要看其他货币）
        for stock_market in stock_markets:
            for forex_market in forex_markets:
                if forex_market.currency in ['EUR', 'JPY', 'CNY']:  # 非美元货币
                    start_time = time.time()

                    try:
                        # 准备数据
                        stock_prices = self._prepare_price_data(stock_market)
                        forex_rates = self._extract_exchange_rates(forex_market)

                        if not forex_rates:
                            continue

                        # 选择主要汇率对
                        usd_pair = None
                        for pair in forex_rates.keys():
                            if pair.startswith('USD') or pair.endswith('USD'):
                                usd_pair = pair
                                break

                        if not usd_pair:
                            continue

                        forex_pair_data = forex_rates[usd_pair]
                        forex_series = pd.Series(
                            forex_pair_data.set_index('timestamp')['rate'],
                            index=pd.to_datetime(forex_pair_data['timestamp'])
                        )

                        # 对齐时间序列
                        aligned_stock, aligned_forex = self._align_time_series(stock_prices, forex_series)

                        if len(aligned_stock) < self.min_data_points:
                            continue

                        # 计算相关性
                        correlation, p_value = pearsonr(aligned_stock, aligned_forex)

                        # 香港作为国际金融中心，股市与某些货币应该有合理的相关性
                        # 例如：与人民币的相关性（内地资金流入）
                        expected_correlation_range = (-0.3, 0.5)  # 允许的范围

                        passed = expected_correlation_range[0] <= correlation <= expected_correlation_range[1]
                        confidence = 1.0 - abs(correlation) if passed else 0.3

                        anomalies = []
                        if not passed:
                            anomaly = AnomalyDetection(
                                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                                timestamp=aligned_stock.index[-1],
                                field_name='unusual_stock_forex_correlation',
                                value=correlation,
                                severity=ValidationSeverity.MEDIUM,
                                confidence=0.6,
                                context={
                                    'stock_market': stock_market.market_name,
                                    'forex_market': forex_market.market_name,
                                    'currency_pair': usd_pair,
                                    'expected_range': expected_correlation_range,
                                    'actual_correlation': correlation
                                }
                            )
                            anomalies.append(anomaly)

                        execution_time = (time.time() - start_time) * 1000

                        result = ValidationResult(
                            validation_type=ValidationType.CROSS_ASSET,
                            market_pair=(stock_market.market_name, forex_market.market_name),
                            passed=passed,
                            confidence=confidence,
                            execution_time_ms=execution_time,
                            details={
                                'correlation': correlation,
                                'p_value': p_value,
                                'currency_pair': usd_pair,
                                'expected_correlation_range': expected_correlation_range,
                                'data_points': len(aligned_stock)
                            },
                            anomalies=anomalies
                        )
                        results.append(result)

                    except Exception as e:
                        results.append(ValidationResult(
                            validation_type=ValidationType.CROSS_ASSET,
                            market_pair=(stock_market.market_name, forex_market.market_name),
                            passed=False,
                            confidence=0.0,
                            execution_time_ms=(time.time() - start_time) * 1000,
                            error_message=str(e)
                        ))

        return results

    async def _validate_stock_commodity_relationships(self, stock_markets: List[MarketData], commodity_markets: List[MarketData]) -> List[ValidationResult]:
        """验证股票-商品关系"""
        results = []

        # 香港股市与大宗商品（如石油、黄金）的关系
        for stock_market in stock_markets:
            for commodity_market in commodity_markets:
                start_time = time.time()

                try:
                    # 准备数据
                    stock_prices = self._prepare_price_data(stock_market)
                    commodity_prices = self._prepare_price_data(commodity_market)

                    # 对齐时间序列
                    aligned_stock, aligned_commodity = self._align_time_series(stock_prices, commodity_prices)

                    if len(aligned_stock) < self.min_data_points:
                        continue

                    # 计算相关性
                    correlation, p_value = pearsonr(aligned_stock, aligned_commodity)

                    # 一般情况下，股票与商品价格的相关性不应该过高
                    max_reasonable_correlation = 0.4

                    passed = abs(correlation) <= max_reasonable_correlation
                    confidence = 1.0 - abs(correlation) / max_reasonable_correlation if passed else 0.3

                    anomalies = []
                    if abs(correlation) > max_reasonable_correlation:
                        anomaly = AnomalyDetection(
                            anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                            timestamp=aligned_stock.index[-1],
                            field_name='unusual_stock_commodity_correlation',
                            value=correlation,
                            severity=ValidationSeverity.MEDIUM,
                            confidence=0.6,
                            context={
                                'stock_market': stock_market.market_name,
                                'commodity_market': commodity_market.market_name,
                                'max_reasonable_correlation': max_reasonable_correlation,
                                'actual_correlation': correlation
                            }
                        )
                        anomalies.append(anomaly)

                    execution_time = (time.time() - start_time) * 1000

                    result = ValidationResult(
                        validation_type=ValidationType.CROSS_ASSET,
                        market_pair=(stock_market.market_name, commodity_market.market_name),
                        passed=passed,
                        confidence=confidence,
                        execution_time_ms=execution_time,
                        details={
                            'correlation': correlation,
                            'p_value': p_value,
                            'max_reasonable_correlation': max_reasonable_correlation,
                            'data_points': len(aligned_stock)
                        },
                        anomalies=anomalies
                    )
                    results.append(result)

                except Exception as e:
                    results.append(ValidationResult(
                        validation_type=ValidationType.CROSS_ASSET,
                        market_pair=(stock_market.market_name, commodity_market.market_name),
                        passed=False,
                        confidence=0.0,
                        execution_time_ms=(time.time() - start_time) * 1000,
                        error_message=str(e)
                    ))

        return results

    # 辅助方法
    def _prepare_price_data(self, market: MarketData) -> pd.Series:
        """准备价格数据"""
        if self.price_column in market.data.columns:
            prices = market.data[self.price_column]
        elif 'close' in market.data.columns:
            prices = market.data['close']
        elif 'price' in market.data.columns:
            prices = market.data['price']
        else:
            # 寻找数值列
            numeric_cols = market.data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                prices = market.data[numeric_cols[0]]
            else:
                raise ValueError("No price column found")

        # 设置时间索引
        if market.timestamp_col in market.data.columns:
            timestamps = pd.to_datetime(market.data[market.timestamp_col])
            return pd.Series(prices.values, index=timestamps)
        else:
            return pd.Series(prices.values)

    def _align_time_series(self, series1: pd.Series, series2: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """对齐时间序列"""
        common_index = series1.index.intersection(series2.index)
        if len(common_index) == 0:
            return pd.Series(), pd.Series()

        return series1.loc[common_index], series2.loc[common_index]

    def _extract_exchange_rates(self, market: MarketData) -> Dict[str, pd.DataFrame]:
        """提取汇率数据"""
        rates = {}

        # 假设外汇数据格式包含 'pair' 和 'rate' 列
        if 'pair' in market.data.columns and 'rate' in market.data.columns:
            for pair in market.data['pair'].unique():
                pair_data = market.data[market.data['pair'] == pair].copy()
                if market.timestamp_col in pair_data.columns:
                    pair_data['timestamp'] = pd.to_datetime(pair_data[market.timestamp_col])
                    rates[pair] = pair_data[['timestamp', 'rate']]

        return rates

    def _variance_ratio_test(self, returns: pd.Series, q: int = 2) -> float:
        """方差比检验"""
        n = len(returns)
        if n < q * 2:
            return 1.0

        # 计算不同时间间隔的方差
        var_1 = returns.var()
        var_q = returns.rolling(window=q).sum().dropna().var()

        # 方差比
        variance_ratio = var_q / (q * var_1) if var_1 > 0 else 1.0

        return variance_ratio

    def _runs_test(self, prices: pd.Series) -> Dict[str, Any]:
        """运行检验（随机游走测试）"""
        # 计算价格变化
        price_changes = prices.diff().dropna()

        # 将变化转换为正负号
        signs = np.sign(price_changes)
        signs = signs[signs != 0]  # 移除0值

        if len(signs) < 10:
            return {'p_value': 1.0, 'statistic': 0}

        # 计算游程数
        runs = 1
        for i in range(1, len(signs)):
            if signs[i] != signs[i-1]:
                runs += 1

        # 计算期望游程数和方差
        n1 = np.sum(signs > 0)  # 正变化数量
        n2 = np.sum(signs < 0)  # 负变化数量
        n = n1 + n2

        expected_runs = (2 * n1 * n2) / n + 1
        var_runs = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n ** 2 * (n - 1))

        # 计算Z统计量
        if var_runs > 0:
            z_statistic = (runs - expected_runs) / np.sqrt(var_runs)
            # 计算p值（双边检验）
            p_value = 2 * (1 - stats.norm.cdf(abs(z_statistic)))
        else:
            z_statistic = 0
            p_value = 1.0

        return {
            'runs': runs,
            'expected_runs': expected_runs,
            'statistic': z_statistic,
            'p_value': p_value
        }


# Factory function
def create_cross_market_validator(config: Optional[Dict[str, Any]] = None) -> CrossMarketValidator:
    """创建跨市场验证器"""
    return CrossMarketValidator(config)


# Export
__all__ = [
    'CrossMarketValidator',
    'ValidationType',
    'ValidationResult',
    'MarketData',
    'create_cross_market_validator'
]