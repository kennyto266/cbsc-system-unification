"""
Data Factory
數據工廠

Factory pattern for creating and managing different types of data adapters
including market data, economic data, and alternative data sources.
"""

from typing import Dict, Type, Optional, Any, Union, List
from abc import ABC, abstractmethod
from datetime import datetime
import asyncio
import logging
import os
from enum import Enum

try:
    from .market_data_adapter import MarketDataAdapter, MarketDataConfig, get_market_adapter
except ImportError:
    MarketDataAdapter = None
    MarketDataConfig = None
    get_market_adapter = None

from .economic_data_adapter import EconomicDataAdapter, get_economic_data_adapter

try:
    from ..collectors.market_data_collector import MarketDataCollector, CollectorConfig
except ImportError:
    MarketDataCollector = None
    CollectorConfig = None

try:
    from ..services.influxdb_client import InfluxDBManager
except ImportError:
    InfluxDBManager = None

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Enumeration of supported data source types"""
    MARKET_DATA = "market_data"
    ECONOMIC_DATA = "economic_data"
    ALTERNATIVE_DATA = "alternative_data"
    FUNDAMENTAL_DATA = "fundamental_data"
    REAL_TIME_DATA = "real_time_data"


class DataProvider(Enum):
    """Enumeration of data providers"""
    YAHOO_FINANCE = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    INFLUXDB = "influxdb"
    CSV_FILES = "csv"
    DATABASE = "database"
    API_CUSTOM = "api_custom"


class IDataAdapter(ABC):
    """Interface for all data adapters"""

    @abstractmethod
    async def get_data(self, symbol: str, start_date: datetime, end_date: datetime, **kwargs) -> Optional[Any]:
        """Get data for the specified parameters"""
        pass

    @abstractmethod
    async def get_latest_data(self, symbol: str, **kwargs) -> Optional[Any]:
        """Get latest data for the specified symbol"""
        pass

    @abstractmethod
    async def get_multiple_symbols(self, symbols: list, start_date: datetime, end_date: datetime, **kwargs) -> Dict[str, Any]:
        """Get data for multiple symbols"""
        pass

    @abstractmethod
    def clear_cache(self):
        """Clear adapter cache"""
        pass


class MarketDataAdapterWrapper(IDataAdapter):
    """Wrapper for MarketDataAdapter implementing IDataAdapter interface"""

    def __init__(self, adapter: MarketDataAdapter):
        self.adapter = adapter

    async def get_data(self, symbol: str, start_date: datetime, end_date: datetime, **kwargs) -> Optional[Any]:
        """Get market data"""
        interval = kwargs.get('interval', '1d')
        return await self.adapter.get_price_data(symbol, start_date, end_date, interval)

    async def get_latest_data(self, symbol: str, **kwargs) -> Optional[Any]:
        """Get latest market data"""
        return await self.adapter.get_latest_price(symbol)

    async def get_multiple_symbols(self, symbols: list, start_date: datetime, end_date: datetime, **kwargs) -> Dict[str, Any]:
        """Get market data for multiple symbols"""
        interval = kwargs.get('interval', '1d')
        return await self.adapter.get_multiple_symbols(symbols, start_date, end_date, interval)

    def clear_cache(self):
        """Clear market data cache"""
        self.adapter.clear_cache()


class EconomicDataAdapterWrapper(IDataAdapter):
    """Wrapper for EconomicDataAdapter implementing IDataAdapter interface"""

    def __init__(self, adapter: EconomicDataAdapter):
        self.adapter = adapter

    async def get_data(self, symbol: str, start_date: datetime, end_date: datetime, **kwargs) -> Optional[Any]:
        """Get economic data"""
        data_type = kwargs.get('data_type', 'all')

        if data_type == 'hibor':
            return self.adapter.get_hibor_data(start_date, end_date)
        elif data_type == 'gdp':
            frequency = kwargs.get('frequency', 'quarterly')
            return self.adapter.get_gdp_data(start_date, end_date, frequency)
        elif data_type == 'visitor':
            return self.adapter.get_visitor_arrivals_data(start_date, end_date)
        elif data_type == 'pmi':
            return self.adapter.get_pmi_data(start_date, end_date)
        elif data_type == 'unemployment':
            return self.adapter.get_unemployment_data(start_date, end_date)
        else:
            return self.adapter.get_all_economic_data(start_date, end_date)

    async def get_latest_data(self, symbol: str, **kwargs) -> Optional[Any]:
        """Get latest economic data"""
        # Economic data is typically not real-time, so get recent data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        return await self.get_data(symbol, start_date, end_date, **kwargs)

    async def get_multiple_symbols(self, symbols: list, start_date: datetime, end_date: datetime, **kwargs) -> Dict[str, Any]:
        """Get economic data for multiple indicators"""
        results = {}
        data_type = kwargs.get('data_type', 'all')

        if data_type == 'all':
            data = self.adapter.get_all_economic_data(start_date, end_date)
            if data is not None:
                results['all_economic'] = data
        else:
            for symbol in symbols:
                data = await self.get_data(symbol, start_date, end_date, **kwargs)
                if data is not None:
                    results[symbol] = data

        return results

    def clear_cache(self):
        """Clear economic data cache"""
        self.adapter.clear_cache()


class AlternativeDataAdapter(IDataAdapter):
    """Adapter for alternative data sources (social media sentiment, news, etc.)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = {}

    async def get_data(self, symbol: str, start_date: datetime, end_date: datetime, **kwargs) -> Optional[Any]:
        """Get alternative data"""
        data_type = kwargs.get('data_type', 'sentiment')

        if data_type == 'sentiment':
            return await self._get_sentiment_data(symbol, start_date, end_date)
        elif data_type == 'news':
            return await self._get_news_data(symbol, start_date, end_date)
        elif data_type == 'social':
            return await self._get_social_media_data(symbol, start_date, end_date)
        else:
            logger.warning(f"Unknown alternative data type: {data_type}")
            return None

    async def get_latest_data(self, symbol: str, **kwargs) -> Optional[Any]:
        """Get latest alternative data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        return await self.get_data(symbol, start_date, end_date, **kwargs)

    async def get_multiple_symbols(self, symbols: list, start_date: datetime, end_date: datetime, **kwargs) -> Dict[str, Any]:
        """Get alternative data for multiple symbols"""
        results = {}

        for symbol in symbols:
            data = await self.get_data(symbol, start_date, end_date, **kwargs)
            if data is not None:
                results[symbol] = data

        return results

    def clear_cache(self):
        """Clear alternative data cache"""
        self.cache.clear()

    async def _get_sentiment_data(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[Any]:
        """Get sentiment data"""
        # Placeholder implementation
        logger.warning("Sentiment data collection not implemented")
        return None

    async def _get_news_data(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[Any]:
        """Get news data"""
        # Placeholder implementation
        logger.warning("News data collection not implemented")
        return None

    async def _get_social_media_data(self, symbol: str, start_date: datetime, end_date: datetime) -> Optional[Any]:
        """Get social media data"""
        # Placeholder implementation
        logger.warning("Social media data collection not implemented")
        return None


class RealTimeDataAdapter(IDataAdapter):
    """Adapter for real-time data streaming"""

    def __init__(self, collector: MarketDataCollector):
        self.collector = collector

    async def get_data(self, symbol: str, start_date: datetime, end_date: datetime, **kwargs) -> Optional[Any]:
        """Get real-time data"""
        # For real-time adapter, we would query the live data stream
        logger.warning("Real-time historical data query not implemented")
        return None

    async def get_latest_data(self, symbol: str, **kwargs) -> Optional[Any]:
        """Get latest real-time data"""
        try:
            # Get latest price from the collector's data sources
            if hasattr(self.collector, '_get_symbol_data'):
                data = await self.collector._get_symbol_data(symbol)
                if data and data:
                    # Return the most recent data point
                    latest = data[-1]
                    return {
                        'symbol': symbol,
                        'price': latest['fields']['close'],
                        'timestamp': latest['timestamp'],
                        'volume': latest['fields']['volume'],
                        'source': latest['tags']['data_source']
                    }
        except Exception as e:
            logger.error(f"Failed to get real-time data for {symbol}: {e}")

        return None

    async def get_multiple_symbols(self, symbols: list, start_date: datetime, end_date: datetime, **kwargs) -> Dict[str, Any]:
        """Get real-time data for multiple symbols"""
        results = {}

        for symbol in symbols:
            data = await self.get_latest_data(symbol, **kwargs)
            if data is not None:
                results[symbol] = data

        return results

    def clear_cache(self):
        """Clear real-time data cache"""
        # Real-time adapter typically doesn't use cache
        pass


class DataAdapterFactory:
    """
    Factory for creating and managing data adapters
    """

    _adapters: Dict[DataSourceType, Dict[str, IDataAdapter]] = {}
    _instances: Dict[str, Any] = {}

    @classmethod
    async def create_adapter(
        cls,
        source_type: DataSourceType,
        provider: DataProvider = DataProvider.YAHOO_FINANCE,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> IDataAdapter:
        """
        Create a data adapter based on type and provider

        Args:
            source_type: Type of data source
            provider: Data provider to use
            config: Configuration dictionary
            **kwargs: Additional parameters

        Returns:
            Configured data adapter instance
        """
        if config is None:
            config = {}

        cache_key = f"{source_type.value}_{provider.value}"

        # Check if adapter already exists
        if cache_key in cls._adapters.get(source_type, {}):
            return cls._adapters[source_type][cache_key]

        # Create new adapter based on type and provider
        adapter = None

        if source_type == DataSourceType.MARKET_DATA:
            adapter = await cls._create_market_adapter(provider, config, **kwargs)
        elif source_type == DataSourceType.ECONOMIC_DATA:
            adapter = await cls._create_economic_adapter(provider, config, **kwargs)
        elif source_type == DataSourceType.ALTERNATIVE_DATA:
            adapter = await cls._create_alternative_adapter(provider, config, **kwargs)
        elif source_type == DataSourceType.REAL_TIME_DATA:
            adapter = await cls._create_realtime_adapter(provider, config, **kwargs)
        else:
            raise ValueError(f"Unsupported data source type: {source_type}")

        # Cache the adapter
        if source_type not in cls._adapters:
            cls._adapters[source_type] = {}
        cls._adapters[source_type][cache_key] = adapter

        logger.info(f"Created {source_type.value} adapter for {provider.value}")

        return adapter

    @classmethod
    async def _create_market_adapter(cls, provider: DataProvider, config: Dict[str, Any], **kwargs) -> MarketDataAdapterWrapper:
        """Create market data adapter"""
        if MarketDataAdapter is None or MarketDataConfig is None or get_market_adapter is None:
            raise ImportError("Market data adapter dependencies not available")

        market_config = MarketDataConfig(
            primary_source=provider.value,
            api_key=config.get('api_key'),
            base_url=config.get('base_url'),
            cache_enabled=config.get('cache_enabled', True),
            cache_ttl=config.get('cache_ttl', 300)
        )

        # Get InfluxDB manager if available
        influxdb_manager = kwargs.get('influxdb_manager')

        adapter = get_market_adapter(market_config, influxdb_manager)
        return MarketDataAdapterWrapper(adapter)

    @classmethod
    async def _create_economic_adapter(cls, provider: DataProvider, config: Dict[str, Any], **kwargs) -> EconomicDataAdapterWrapper:
        """Create economic data adapter"""
        # For now, economic adapter is singleton
        adapter = get_economic_data_adapter()
        return EconomicDataAdapterWrapper(adapter)

    @classmethod
    async def _create_alternative_adapter(cls, provider: DataProvider, config: Dict[str, Any], **kwargs) -> AlternativeDataAdapter:
        """Create alternative data adapter"""
        adapter = AlternativeDataAdapter(config)
        return adapter

    @classmethod
    async def _create_realtime_adapter(cls, provider: DataProvider, config: Dict[str, Any], **kwargs) -> RealTimeDataAdapter:
        """Create real-time data adapter"""
        if MarketDataCollector is None or CollectorConfig is None:
            raise ImportError("Market data collector dependencies not available")

        # Create market data collector
        collector_config = CollectorConfig(
            symbols=config.get('symbols', []),
            collection_interval=config.get('collection_interval', 60),
            market_hours_only=config.get('market_hours_only', True)
        )

        influxdb_manager = kwargs.get('influxdb_manager')
        if not influxdb_manager:
            raise ValueError("InfluxDB manager required for real-time data adapter")

        collector = MarketDataCollector(
            config=collector_config,
            influxdb_manager=influxdb_manager
        )

        # Start the collector if not already running
        if not collector._running:
            await collector.start()

        return RealTimeDataAdapter(collector)

    @classmethod
    def get_adapter(
        cls,
        source_type: DataSourceType,
        provider: Optional[DataProvider] = None
    ) -> Optional[IDataAdapter]:
        """
        Get existing adapter

        Args:
            source_type: Type of data source
            provider: Data provider (optional)

        Returns:
            Existing adapter instance or None
        """
        if source_type not in cls._adapters:
            return None

        if provider is None:
            # Return any available adapter for this type
            adapters = list(cls._adapters[source_type].values())
            return adapters[0] if adapters else None

        cache_key = f"{source_type.value}_{provider.value}"
        return cls._adapters[source_type].get(cache_key)

    @classmethod
    def list_adapters(cls) -> Dict[DataSourceType, List[str]]:
        """List all available adapters"""
        result = {}
        for source_type, adapters in cls._adapters.items():
            result[source_type] = list(adapters.keys())
        return result

    @classmethod
    def clear_adapter_cache(cls, source_type: Optional[DataSourceType] = None):
        """Clear adapter cache"""
        if source_type is None:
            # Clear all
            for adapters in cls._adapters.values():
                for adapter in adapters.values():
                    adapter.clear_cache()
        elif source_type in cls._adapters:
            for adapter in cls._adapters[source_type].values():
                adapter.clear_cache()

    @classmethod
    async def create_from_config(cls, config_dict: Dict[str, Any]) -> Dict[str, IDataAdapter]:
        """
        Create multiple adapters from configuration

        Args:
            config_dict: Configuration dictionary

        Returns:
            Dictionary of created adapters
        """
        adapters = {}

        for adapter_name, adapter_config in config_dict.items():
            try:
                source_type = DataSourceType(adapter_config['type'])
                provider = DataProvider(adapter_config['provider'])

                adapter = await cls.create_adapter(
                    source_type=source_type,
                    provider=provider,
                    config=adapter_config.get('config', {}),
                    **adapter_config.get('kwargs', {})
                )

                adapters[adapter_name] = adapter

            except Exception as e:
                logger.error(f"Failed to create adapter {adapter_name}: {e}")

        return adapters


# Convenience functions
async def get_market_data_adapter(
    provider: DataProvider = DataProvider.YAHOO_FINANCE,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> MarketDataAdapterWrapper:
    """Get market data adapter"""
    return await DataAdapterFactory.create_adapter(
        DataSourceType.MARKET_DATA,
        provider,
        config,
        **kwargs
    )


async def get_economic_data_adapter(
    provider: DataProvider = DataProvider.CSV_FILES,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> EconomicDataAdapterWrapper:
    """Get economic data adapter"""
    return await DataAdapterFactory.create_adapter(
        DataSourceType.ECONOMIC_DATA,
        provider,
        config,
        **kwargs
    )


async def get_realtime_data_adapter(
    provider: DataProvider = DataProvider.INFLUXDB,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> RealTimeDataAdapter:
    """Get real-time data adapter"""
    return await DataAdapterFactory.create_adapter(
        DataSourceType.REAL_TIME_DATA,
        provider,
        config,
        **kwargs
    )


__all__ = [
    'DataAdapterFactory',
    'IDataAdapter',
    'DataSourceType',
    'DataProvider',
    'MarketDataAdapterWrapper',
    'EconomicDataAdapterWrapper',
    'AlternativeDataAdapter',
    'RealTimeDataAdapter',
    'get_market_data_adapter',
    'get_economic_data_adapter',
    'get_realtime_data_adapter'
]