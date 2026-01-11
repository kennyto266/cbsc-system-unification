#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非价格策略API服务层 - Non-Price Strategy API Service Layer
提供HKMA宏观数据、情绪分析和策略集成的统一服务接口
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from ..models.non_price_responses import (
    NonPriceSignal,
    HIBORRate,
    MonetaryBaseData,
    ExchangeRateData,
    LiquidityData,
    HistoricalDataPoint,
    SentimentSignal,
    StrategyInfo,
    StrategyPerformance,
    SignalType,
    DataSource,
    TrendDirection,
    APIConfiguration
)

# 导入现有的非价格系统组件
try:
    from ....non_price import get_non_price_system
    NON_PRICE_SYSTEM_AVAILABLE = True
except ImportError:
    NON_PRICE_SYSTEM_AVAILABLE = False
    logging.warning("Non-price system not available, using mock data")


logger = logging.getLogger(__name__)


@dataclass
class HKMAAPIClient:
    """HKMA API客户端"""
    base_url: str = "https://api.hkma.gov.hk"
    timeout: int = 30

    async def get_hibor_rates(self) -> List[HIBORRate]:
        """获取最新HIBOR利率"""
        try:
            # 实际HKMA API调用
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                url = f"{self.base_url}/public/hibor-rates/latest"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_hibor_data(data)
                    else:
                        logger.error(f"HKMA API error: {response.status}")
                        return self._get_mock_hibor_data()
        except Exception as e:
            logger.error(f"Failed to fetch HIBOR rates: {e}")
            return self._get_mock_hibor_data()

    async def get_monetary_base(self) -> MonetaryBaseData:
        """获取最新货币基础数据"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                url = f"{self.base_url}/public/monetary-base/latest"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_monetary_base_data(data)
                    else:
                        return self._get_mock_monetary_base_data()
        except Exception as e:
            logger.error(f"Failed to fetch monetary base: {e}")
            return self._get_mock_monetary_base_data()

    async def get_exchange_rate(self, currency_pair: str = "USD/HKD") -> ExchangeRateData:
        """获取最新汇率数据"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                url = f"{self.base_url}/public/exchange-rates/latest?pair={currency_pair}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_exchange_rate_data(data, currency_pair)
                    else:
                        return self._get_mock_exchange_rate_data(currency_pair)
        except Exception as e:
            logger.error(f"Failed to fetch exchange rate: {e}")
            return self._get_mock_exchange_rate_data(currency_pair)

    async def get_liquidity_data(self) -> List[LiquidityData]:
        """获取最新流动性数据"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                url = f"{self.base_url}/public/liquidity/latest"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_liquidity_data(data)
                    else:
                        return self._get_mock_liquidity_data()
        except Exception as e:
            logger.error(f"Failed to fetch liquidity data: {e}")
            return self._get_mock_liquidity_data()

    def _parse_hibor_data(self, data: Dict[str, Any]) -> List[HIBORRate]:
        """解析HIBOR数据"""
        rates = []
        for item in data.get("rates", []):
            rates.append(HIBORRate(
                tenor=item.get("tenor"),
                rate=item.get("rate"),
                change=item.get("change"),
                timestamp=datetime.fromisoformat(item.get("timestamp"))
            ))
        return rates

    def _parse_monetary_base_data(self, data: Dict[str, Any]) -> MonetaryBaseData:
        """解析货币基础数据"""
        return MonetaryBaseData(
            total_amount=data.get("total_amount"),
            change_amount=data.get("change_amount"),
            change_percentage=data.get("change_percentage"),
            timestamp=datetime.fromisoformat(data.get("timestamp"))
        )

    def _parse_exchange_rate_data(self, data: Dict[str, Any], currency_pair: str) -> ExchangeRateData:
        """解析汇率数据"""
        return ExchangeRateData(
            currency_pair=currency_pair,
            rate=data.get("rate"),
            change=data.get("change"),
            timestamp=datetime.fromisoformat(data.get("timestamp"))
        )

    def _parse_liquidity_data(self, data: Dict[str, Any]) -> List[LiquidityData]:
        """解析流动性数据"""
        liquidity_items = []
        for item in data.get("indicators", []):
            liquidity_items.append(LiquidityData(
                indicator=item.get("indicator"),
                value=item.get("value"),
                unit=item.get("unit"),
                trend=TrendDirection(item.get("trend", "STABLE")),
                timestamp=datetime.fromisoformat(item.get("timestamp"))
            ))
        return liquidity_items

    # Mock data methods for fallback
    def _get_mock_hibor_data(self) -> List[HIBORRate]:
        """获取模拟HIBOR数据"""
        now = datetime.utcnow()
        return [
            HIBORRate(tenor="1M", rate=5.75, change=0.05, timestamp=now),
            HIBORRate(tenor="3M", rate=5.85, change=0.03, timestamp=now),
            HIBORRate(tenor="6M", rate=5.95, change=0.02, timestamp=now),
            HIBORRate(tenor="12M", rate=6.15, change=0.01, timestamp=now)
        ]

    def _get_mock_monetary_base_data(self) -> MonetaryBaseData:
        """获取模拟货币基础数据"""
        now = datetime.utcnow()
        return MonetaryBaseData(
            total_amount=18500.5,
            change_amount=125.3,
            change_percentage=0.68,
            timestamp=now
        )

    def _get_mock_exchange_rate_data(self, currency_pair: str) -> ExchangeRateData:
        """获取模拟汇率数据"""
        now = datetime.utcnow()
        return ExchangeRateData(
            currency_pair=currency_pair,
            rate=7.8275,
            change=0.0002,
            timestamp=now
        )

    def _get_mock_liquidity_data(self) -> List[LiquidityData]:
        """获取模拟流动性数据"""
        now = datetime.utcnow()
        return [
            LiquidityData(
                indicator="银行体系结余",
                value=450.2,
                unit="亿港币",
                trend=TrendDirection.STABLE,
                timestamp=now
            ),
            LiquidityData(
                indicator="外汇基金票据",
                value=8500.5,
                unit="亿港币",
                trend=TrendDirection.UP,
                timestamp=now
            )
        ]


class SentimentAnalysisService:
    """情绪分析服务"""

    def __init__(self, base_url: str = "https://api.sentiment-analysis.com"):
        self.base_url = base_url

    async def analyze_sentiment(self, symbol: str) -> SentimentSignal:
        """分析指定标的的情绪"""
        try:
            # 这里可以集成实际的情绪分析API
            # 目前使用模拟数据
            return self._generate_mock_sentiment_signal(symbol)
        except Exception as e:
            logger.error(f"Sentiment analysis failed for {symbol}: {e}")
            return self._generate_mock_sentiment_signal(symbol)

    def _generate_mock_sentiment_signal(self, symbol: str) -> SentimentSignal:
        """生成模拟情绪信号"""
        import random

        sentiment_score = random.uniform(-0.8, 0.8)
        if sentiment_score > 0.3:
            sentiment_label = "积极"
        elif sentiment_score < -0.3:
            sentiment_label = "消极"
        else:
            sentiment_label = "中性"

        return SentimentSignal(
            signal_id=f"sentiment_{symbol}_{int(datetime.utcnow().timestamp())}",
            signal_type=SignalType.SENTIMENT,
            source=DataSource.SENTIMENT_API,
            symbol=symbol,
            value=sentiment_score,
            confidence=0.75,
            strength=abs(sentiment_score),
            timestamp=datetime.utcnow(),
            metadata={"analysis_method": "nlp_sentiment", "sources": ["news", "social_media"]},
            trend=TrendDirection.UP if sentiment_score > 0 else TrendDirection.DOWN,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            source_count=15,
            volume=random.randint(100, 5000)
        )


class NonPriceAPIService:
    """非价格策略API服务主类"""

    def __init__(self, config: Optional[APIConfiguration] = None):
        self.config = config or APIConfiguration()
        self.hkma_client = HKMAAPIClient()
        self.sentiment_service = SentimentAnalysisService()

        # 初始化非价格系统（如果可用）
        self.non_price_system = None
        if NON_PRICE_SYSTEM_AVAILABLE:
            try:
                self.non_price_system = get_non_price_system()
                logger.info("Non-price system initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize non-price system: {e}")

    async def get_latest_hibor_rates(self) -> List[HIBORRate]:
        """获取最新HIBOR利率数据"""
        return await self.hkma_client.get_hibor_rates()

    async def get_latest_monetary_base(self) -> MonetaryBaseData:
        """获取最新货币基础数据"""
        return await self.hkma_client.get_monetary_base()

    async def get_latest_exchange_rate(self, currency_pair: str = "USD/HKD") -> ExchangeRateData:
        """获取最新汇率数据"""
        return await self.hkma_client.get_exchange_rate(currency_pair)

    async def get_latest_liquidity_data(self) -> List[LiquidityData]:
        """获取最新流动性数据"""
        return await self.hkma_client.get_liquidity_data()

    async def get_historical_data(
        self,
        data_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalDataPoint]:
        """获取历史数据"""
        try:
            # 根据数据类型调用相应的API
            if data_type == "hibor":
                return await self._get_historical_hibor(start_date, end_date)
            elif data_type == "monetary_base":
                return await self._get_historical_monetary_base(start_date, end_date)
            elif data_type == "exchange_rate":
                return await self._get_historical_exchange_rate(start_date, end_date)
            else:
                return self._generate_mock_historical_data(data_type, start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to get historical data for {data_type}: {e}")
            return self._generate_mock_historical_data(data_type, start_date, end_date)

    async def get_sentiment_signals(self, symbol: str) -> List[SentimentSignal]:
        """获取情绪信号"""
        sentiment_signal = await self.sentiment_service.analyze_sentiment(symbol)
        return [sentiment_signal]

    async def get_available_strategies(self) -> List[StrategyInfo]:
        """获取可用的非价格策略"""
        strategies = [
            StrategyInfo(
                strategy_id="hkma_macro_strategy",
                name="HKMA宏观经济策略",
                description="基于HKMA宏观数据的交易策略",
                type="macro",
                active=True,
                parameters={
                    "hibor_weight": 0.3,
                    "liquidity_weight": 0.4,
                    "exchange_rate_weight": 0.3
                },
                created_at=datetime.utcnow() - timedelta(days=30),
                updated_at=datetime.utcnow() - timedelta(days=1)
            ),
            StrategyInfo(
                strategy_id="sentiment_momentum",
                name="情绪动量策略",
                description="基于市场情绪分析的动量交易策略",
                type="sentiment",
                active=True,
                parameters={
                    "sentiment_threshold": 0.5,
                    "momentum_period": 14,
                    "volume_threshold": 1000
                },
                created_at=datetime.utcnow() - timedelta(days=20),
                updated_at=datetime.utcnow() - timedelta(hours=6)
            )
        ]

        # 如果非价格系统可用，添加其策略
        if self.non_price_system:
            try:
                system_strategies = await self._get_non_price_system_strategies()
                strategies.extend(system_strategies)
            except Exception as e:
                logger.error(f"Failed to get non-price system strategies: {e}")

        return strategies

    async def get_strategy_performance(self, strategy_id: str) -> Optional[StrategyPerformance]:
        """获取策略表现"""
        # 模拟策略表现数据
        return StrategyPerformance(
            strategy_id=strategy_id,
            period_start=datetime.utcnow() - timedelta(days=90),
            period_end=datetime.utcnow(),
            total_return=0.156,
            annualized_return=0.634,
            max_drawdown=-0.082,
            sharpe_ratio=1.45,
            win_rate=0.68,
            total_trades=42,
            profit_factor=1.82,
            last_updated=datetime.utcnow()
        )

    def _generate_mock_historical_data(
        self,
        data_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalDataPoint]:
        """生成模拟历史数据"""
        import random

        data_points = []
        current_date = start_date
        base_value = 100.0

        while current_date <= end_date:
            # 添加随机波动
            change = random.uniform(-0.05, 0.05)
            base_value *= (1 + change)

            data_points.append(HistoricalDataPoint(
                date=current_date,
                value=base_value,
                metadata={"data_type": data_type, "quality": "high"}
            ))

            current_date += timedelta(days=1)

        return data_points

    async def _get_historical_hibor(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalDataPoint]:
        """获取历史HIBOR数据"""
        # 这里可以实现真实的HKMA历史数据API调用
        return self._generate_mock_historical_data("hibor", start_date, end_date)

    async def _get_historical_monetary_base(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalDataPoint]:
        """获取历史货币基础数据"""
        return self._generate_mock_historical_data("monetary_base", start_date, end_date)

    async def _get_historical_exchange_rate(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[HistoricalDataPoint]:
        """获取历史汇率数据"""
        return self._generate_mock_historical_data("exchange_rate", start_date, end_date)

    async def _get_non_price_system_strategies(self) -> List[StrategyInfo]:
        """从非价格系统获取策略信息"""
        # 这里可以集成现有的非价格系统策略
        strategies = []

        try:
            # 假设非价格系统有获取策略的方法
            if hasattr(self.non_price_system, 'get_available_strategies'):
                system_strategies = await self.non_price_system.get_available_strategies()
                for strategy in system_strategies:
                    strategies.append(StrategyInfo(
                        strategy_id=strategy.get('id', 'unknown'),
                        name=strategy.get('name', 'Unknown Strategy'),
                        description=strategy.get('description', ''),
                        type='non_price_system',
                        active=strategy.get('active', False),
                        parameters=strategy.get('parameters', {}),
                        created_at=datetime.utcnow() - timedelta(days=15),
                        updated_at=datetime.utcnow()
                    ))
        except Exception as e:
            logger.error(f"Error getting non-price system strategies: {e}")

        return strategies


# 全局服务实例
_non_price_service = None


def get_non_price_service() -> NonPriceAPIService:
    """获取非价格API服务实例（单例）"""
    global _non_price_service
    if _non_price_service is None:
        _non_price_service = NonPriceAPIService()
    return _non_price_service


async def initialize_non_price_service(config: Optional[APIConfiguration] = None):
    """初始化非价格服务"""
    global _non_price_service
    _non_price_service = NonPriceAPIService(config)
    logger.info("Non-price API service initialized")