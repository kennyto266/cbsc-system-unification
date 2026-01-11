"""
统一数据管道

协调价格和非价格数据的获取、验证、缓存和同步，提供统一的数据访问接口。

Task #31: Data Flow Unification - Price and Non-Price Integration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

from src.unified.models import (
    DataSource, DataType, UnifiedDataPointSchema, UnifiedDataSeriesSchema,
    PriceDataSchema, HKMADataSchema, SentimentDataSchema, AlternativeDataSchema
)
from src.unified.cache_manager import unified_cache_manager
from src.unified.quality_validator import data_quality_validator
from src.unified.data_synchronizer import data_synchronizer

logger = logging.getLogger(__name__)

@dataclass
class DataRequest:
    """数据请求"""
    symbols: List[str]
    start_time: datetime
    end_time: datetime
    sources: List[DataSource]
    include_quality: bool = True
    cache_fallback: bool = True
    max_retries: int = 3

class DataSourceAdapter(ABC):
    """数据源适配器基类"""

    @abstractmethod
    async def fetch_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """获取数据"""
        pass

    @abstractmethod
    def get_source_type(self) -> DataSource:
        """获取数据源类型"""
        pass

class PriceDataAdapter(DataSourceAdapter):
    """价格数据适配器"""

    def get_source_type(self) -> DataSource:
        return DataSource.PRICE

    async def fetch_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """获取价格数据"""
        try:
            # 这里应该调用实际的价格数据源，如Yahoo Finance API
            # 为了演示，返回模拟数据
            return await self._fetch_mock_price_data(symbol, start_time, end_time)

        except Exception as e:
            logger.error(f"获取价格数据失败 {symbol}: {e}")
            return []

    async def _fetch_mock_price_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """获取模拟价格数据"""
        data_points = []
        current_time = start_time
        base_price = 100.0

        while current_time <= end_time:
            # 生成模拟OHLCV数据
            price_variation = (hash(f"{symbol}{current_time.date()}") % 10 - 5) * 0.01
            open_price = base_price + price_variation
            close_price = open_price + (hash(f"{symbol}{current_time.hour}") % 5 - 2.5) * 0.5
            high_price = max(open_price, close_price) + abs(hash(f"{symbol}{current_time.minute}") % 3) * 0.2
            low_price = min(open_price, close_price) - abs(hash(f"{symbol}{current_time.second}") % 2) * 0.2
            volume = abs(hash(f"{symbol}{current_time}") % 1000000) + 100000

            data_point = {
                'timestamp': current_time.isoformat(),
                'symbol': symbol,
                'source': DataSource.PRICE,
                'data_type': DataType.OHLCV,
                'open_price': round(open_price, 2),
                'high_price': round(high_price, 2),
                'low_price': round(low_price, 2),
                'close_price': round(close_price, 2),
                'volume': volume,
                'metadata': {
                    'provider': 'mock_price_adapter',
                    'fetch_time': datetime.now().isoformat()
                }
            }

            data_points.append(data_point)
            current_time += timedelta(hours=1)
            base_price = close_price

        return data_points

class HKMADataAdapter(DataSourceAdapter):
    """HKMA数据适配器"""

    def get_source_type(self) -> DataSource:
        return DataSource.HKMA

    async def fetch_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """获取HKMA数据"""
        try:
            # 这里应该调用实际的HKMA API
            return await self._fetch_mock_hkma_data(symbol, start_time, end_time)

        except Exception as e:
            logger.error(f"获取HKMA数据失败: {e}")
            return []

    async def _fetch_mock_hkma_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """获取模拟HKMA数据"""
        data_points = []
        current_time = start_time

        while current_time <= end_time:
            # 生成模拟HKMA指标数据
            hibor_base = 2.5 + (hash(f"hibor{current_time.date()}") % 100) / 100
            monetary_base = 500000 + (hash(f"mb{current_time.date()}") % 50000)

            data_point = {
                'timestamp': current_time.isoformat(),
                'symbol': 'HKD',
                'source': DataSource.HKMA,
                'data_type': DataType.MACRO,
                'indicator': 'hibor',
                'value': hibor_base,
                'metadata': {
                    'currency': 'HKD',
                    'period_type': 'overnight',
                    'frequency': 'daily',
                    'provider': 'mock_hkma_adapter'
                }
            }

            data_points.append(data_point)

            # 货币基础数据
            mb_point = {
                'timestamp': current_time.isoformat(),
                'symbol': 'HKD',
                'source': DataSource.HKMA,
                'data_type': DataType.MACRO,
                'indicator': 'monetary_base',
                'value': monetary_base,
                'metadata': {
                    'currency': 'HKD',
                    'period_type': 'total',
                    'frequency': 'daily',
                    'provider': 'mock_hkma_adapter'
                }
            }

            data_points.append(mb_point)
            current_time += timedelta(days=1)

        return data_points

class SentimentDataAdapter(DataSourceAdapter):
    """情绪数据适配器"""

    def get_source_type(self) -> DataSource:
        return DataSource.SENTIMENT

    async def fetch_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """获取情绪数据"""
        try:
            return await self._fetch_mock_sentiment_data(symbol, start_time, end_time)

        except Exception as e:
            logger.error(f"获取情绪数据失败 {symbol}: {e}")
            return []

    async def _fetch_mock_sentiment_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """获取模拟情绪数据"""
        data_points = []
        current_time = start_time

        while current_time <= end_time:
            # 生成模拟情绪数据
            sentiment_base = (hash(f"sentiment{symbol}{current_time.date()}") % 200 - 100) / 100
            confidence = 0.6 + (hash(f"conf{symbol}{current_time.date()}") % 40) / 100

            data_point = {
                'timestamp': current_time.isoformat(),
                'symbol': symbol,
                'source': DataSource.SENTIMENT,
                'data_type': DataType.SENTIMENT,
                'value': sentiment_base,
                'metadata': {
                    'sentiment_type': 'news_sentiment',
                    'confidence': confidence,
                    'source_count': abs(hash(f"count{symbol}{current_time.date()}") % 50) + 10,
                    'language': 'en',
                    'provider': 'mock_sentiment_adapter'
                }
            }

            data_points.append(data_point)
            current_time += timedelta(hours=4)

        return data_points

class UnifiedDataPipeline:
    """统一数据管道"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 注册数据源适配器
        self.adapters: Dict[DataSource, DataSourceAdapter] = {
            DataSource.PRICE: PriceDataAdapter(),
            DataSource.HKMA: HKMADataAdapter(),
            DataSource.SENTIMENT: SentimentDataAdapter()
        }

        # 管道配置
        self.pipeline_config = {
            'max_concurrent_fetches': 10,
            'default_cache_ttl': timedelta(minutes=5),
            'quality_check_enabled': True,
            'auto_retry_failed': True,
            'max_retry_attempts': 3
        }

        logger.info("统一数据管道初始化完成")

    def register_adapter(self, adapter: DataSourceAdapter) -> None:
        """注册数据源适配器"""
        source_type = adapter.get_source_type()
        self.adapters[source_type] = adapter
        logger.info(f"注册数据源适配器: {source_type}")

    async def fetch_unified_data(
        self,
        request: DataRequest
    ) -> Dict[str, List[UnifiedDataPointSchema]]:
        """获取统一数据"""
        try:
            self.logger.info(
                f"开始获取统一数据: 股票={len(request.symbols)}, "
                f"数据源={request.sources}, 时间范围={request.start_time}~{request.end_time}"
            )

            unified_data = {}

            # 为每个股票获取数据
            for symbol in request.symbols:
                symbol_data = await self._fetch_symbol_data(symbol, request)
                if symbol_data:
                    unified_data[symbol] = symbol_data

            # 记录获取结果
            total_points = sum(len(data) for data in unified_data.values())
            self.logger.info(f"统一数据获取完成: {len(unified_data)}只股票, {total_points}个数据点")

            return unified_data

        except Exception as e:
            self.logger.error(f"获取统一数据失败: {e}")
            raise

    async def _fetch_symbol_data(
        self,
        symbol: str,
        request: DataRequest
    ) -> List[UnifiedDataPointSchema]:
        """获取单个股票的数据"""
        symbol_data = []

        # 并发获取各数据源的数据
        fetch_tasks = []
        for source in request.sources:
            if source in self.adapters:
                task = self._fetch_source_data(symbol, source, request)
                fetch_tasks.append(task)

        source_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # 处理结果
        for i, result in enumerate(source_results):
            if isinstance(result, Exception):
                self.logger.error(f"数据源获取失败 {request.sources[i]}: {result}")
                continue

            if result:
                symbol_data.extend(result)

        # 按时间戳排序
        symbol_data.sort(key=lambda x: x.timestamp)

        # 质量检查
        if request.include_quality and self.pipeline_config['quality_check_enabled']:
            await self._perform_quality_check(symbol_data, symbol)

        return symbol_data

    async def _fetch_source_data(
        self,
        symbol: str,
        source: DataSource,
        request: DataRequest
    ) -> List[UnifiedDataPointSchema]:
        """获取单个数据源的数据"""
        try:
            adapter = self.adapters[source]

            # 首先尝试从缓存获取
            cached_data = await self._get_from_cache(symbol, source, request.start_time, request.end_time)
            if cached_data and not cached_data:  # 缓存为空时继续获取
                cached_data = None

            if cached_data:
                self.logger.debug(f"缓存命中: {symbol}:{source}")
                return cached_data

            # 从数据源获取
            raw_data = await adapter.fetch_data(symbol, request.start_time, request.end_time)

            # 转换为统一格式
            unified_data = await self._convert_to_unified_format(raw_data, source)

            # 缓存数据
            if unified_data:
                await self._cache_data(symbol, source, unified_data)

            return unified_data

        except Exception as e:
            self.logger.error(f"获取数据源数据失败 {symbol}:{source}: {e}")

            if request.cache_fallback:
                # 尝试获取过期的缓存数据作为后备
                return await self._get_stale_cache(symbol, source)

            return []

    async def _convert_to_unified_format(
        self,
        raw_data: List[Dict[str, Any]],
        source: DataSource
    ) -> List[UnifiedDataPointSchema]:
        """转换为统一数据格式"""
        unified_data = []

        for data_point in raw_data:
            try:
                if source == DataSource.PRICE:
                    schema = PriceDataSchema(**data_point)
                elif source == DataSource.HKMA:
                    schema = HKMADataSchema(**data_point)
                elif source == DataSource.SENTIMENT:
                    schema = SentimentDataSchema(**data_point)
                else:
                    # 通用统一数据点
                    schema = UnifiedDataPointSchema(**data_point)

                unified_data.append(schema)

            except Exception as e:
                self.logger.warning(f"数据格式转换失败: {e}, 数据: {data_point}")

        return unified_data

    async def _get_from_cache(
        self,
        symbol: str,
        source: DataSource,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[List[UnifiedDataPointSchema]]:
        """从缓存获取数据"""
        try:
            # 获取缓存的数据序列
            cached_series = await unified_cache_manager.get_unified_series(symbol, source.value)

            if not cached_series:
                return None

            # 过滤时间范围
            filtered_data = []
            for data_point in cached_series:
                point_timestamp = datetime.fromisoformat(data_point.get('timestamp', '').replace('Z', '+00:00'))

                if start_time <= point_timestamp <= end_time:
                    # 转换为统一格式
                    if source == DataSource.PRICE:
                        schema = PriceDataSchema(**data_point)
                    elif source == DataSource.HKMA:
                        schema = HKMADataSchema(**data_point)
                    elif source == DataSource.SENTIMENT:
                        schema = SentimentDataSchema(**data_point)
                    else:
                        schema = UnifiedDataPointSchema(**data_point)

                    filtered_data.append(schema)

            return filtered_data if filtered_data else None

        except Exception as e:
            self.logger.error(f"从缓存获取数据失败: {e}")
            return None

    async def _cache_data(
        self,
        symbol: str,
        source: DataSource,
        data: List[UnifiedDataPointSchema]
    ) -> None:
        """缓存数据"""
        try:
            # 转换为字典格式
            data_dicts = [item.dict() for item in data]

            # 缓存数据序列
            await unified_cache_manager.cache_unified_series(symbol, source.value, data_dicts)

        except Exception as e:
            self.logger.error(f"缓存数据失败: {e}")

    async def _get_stale_cache(
        self,
        symbol: str,
        source: DataSource
    ) -> List[UnifiedDataPointSchema]:
        """获取过期缓存数据作为后备"""
        try:
            # 这里可以实现获取过期缓存的逻辑
            # 目前返回空列表
            return []

        except Exception as e:
            self.logger.error(f"获取过期缓存失败: {e}")
            return []

    async def _perform_quality_check(
        self,
        data: List[UnifiedDataPointSchema],
        symbol: str
    ) -> None:
        """执行质量检查"""
        try:
            if not data:
                return

            # 按数据源分组进行质量检查
            source_groups = {}
            for point in data:
                source = point.source
                if source not in source_groups:
                    source_groups[source] = []
                source_groups[source].append(point.dict())

            for source, points in source_groups.items():
                if points:
                    quality_result = await data_quality_validator.validate_data_quality(
                        points, source, symbol
                    )

                    # 更新数据点的质量评分
                    for point in data:
                        if point.source == source:
                            point.quality_score = quality_result.overall_score
                            point.is_valid = quality_result.quality_level.value >= 3  # ACCEPTABLE及以上

        except Exception as e:
            self.logger.error(f"质量检查失败: {e}")

    async def get_latest_data(
        self,
        symbols: List[str],
        sources: List[DataSource],
        lookback_hours: int = 24
    ) -> Dict[str, Dict[str, UnifiedDataPointSchema]]:
        """获取最新数据"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=lookback_hours)

            request = DataRequest(
                symbols=symbols,
                start_time=start_time,
                end_time=end_time,
                sources=sources
            )

            # 获取数据
            unified_data = await self.fetch_unified_data(request)

            # 提取每个数据源的最新数据点
            latest_data = {}
            for symbol, data_points in unified_data.items():
                latest_data[symbol] = {}

                # 按数据源分组
                source_groups = {}
                for point in data_points:
                    if point.source not in source_groups:
                        source_groups[point.source] = []
                    source_groups[point.source].append(point)

                # 获取每个数据源的最新数据点
                for source, points in source_groups.items():
                    if points:
                        latest_point = max(points, key=lambda x: x.timestamp)
                        latest_data[symbol][source] = latest_point

            return latest_data

        except Exception as e:
            self.logger.error(f"获取最新数据失败: {e}")
            return {}

    async def sync_data(
        self,
        symbols: List[str],
        sources: List[DataSource],
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> str:
        """启动数据同步"""
        try:
            # 转换数据源枚举
            source_values = [s.value for s in sources]

            # 启动同步任务
            task_id = await data_synchronizer.sync_data(
                symbols=symbols,
                sources=source_values,
                start_time=start_time,
                end_time=end_time or datetime.now()
            )

            return task_id

        except Exception as e:
            self.logger.error(f"启动数据同步失败: {e}")
            raise

    def get_sync_status(self, task_id: str):
        """获取同步状态"""
        return data_synchronizer.get_task_status(task_id)

    async def get_data_series(
        self,
        symbol: str,
        source: DataSource,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[UnifiedDataSeriesSchema]:
        """获取数据序列"""
        try:
            request = DataRequest(
                symbols=[symbol],
                sources=[source],
                start_time=start_time,
                end_time=end_time
            )

            unified_data = await self.fetch_unified_data(request)

            if symbol not in unified_data or not unified_data[symbol]:
                return None

            return UnifiedDataSeriesSchema(
                symbol=symbol,
                source=source,
                data_type=DataSource.PRICE if source == DataSource.PRICE else DataType.MACRO,
                start_time=start_time,
                end_time=end_time,
                data_points=unified_data[symbol]
            )

        except Exception as e:
            self.logger.error(f"获取数据序列失败: {e}")
            return None

    def get_pipeline_stats(self) -> Dict[str, Any]:
        """获取管道统计信息"""
        return {
            'registered_adapters': list(self.adapters.keys()),
            'config': self.pipeline_config,
            'cache_stats': asyncio.create_task(unified_cache_manager.get_cache_info()) if hasattr(unified_cache_manager, 'get_cache_info') else None,
            'sync_stats': data_synchronizer.get_sync_stats()
        }

# 创建全局统一数据管道实例
unified_data_pipeline = UnifiedDataPipeline()

# 导出主要类和实例
__all__ = [
    'UnifiedDataPipeline',
    'unified_data_pipeline',
    'DataRequest',
    'DataSourceAdapter',
    'PriceDataAdapter',
    'HKMADataAdapter',
    'SentimentDataAdapter'
]