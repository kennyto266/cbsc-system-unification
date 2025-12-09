"""
數據服務管理器 - 統一管理多個真實數據源

支持Yahoo Finance、Alpha Vantage、CCXT等多個數據源
"""

import asyncio
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .alpha_vantage_adapter import AlphaVantageAdapter
from .base_adapter import (
    BaseDataAdapter,
    DataAdapterConfig,
    DataSourceType,
    DataValidationResult,
    RealMarketData,
)
from .ccxt_crypto_adapter import CCXTCryptoAdapter
from .http_api_adapter import HttpApiDataAdapter
from .raw_data_adapter import RawDataAdapter
from .yahoo_finance_adapter import YahooFinanceAdapter


class DataService:
    """數據服務管理器"""

    def __init__(self, config_path: str = "config / data_adapters.json"):
        self.config_path = config_path
        self.logger = logging.getLogger("hk_quant_system.data_service")
        self.adapters: Dict[str, BaseDataAdapter] = {}
        self.adapter_configs: Dict[str, Dict] = {}
        self._initialized = False

    async def initialize(self) -> bool:
        """初始化數據服務"""
        try:
            self.logger.info("Initializing data service...")

            # 加載配置
            await self._load_config()

            # 初始化適配器
            await self._initialize_adapters()

            self._initialized = True
            self.logger.info("Data service initialized successfully")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to initialize data service: {e}")
            return False

    async def _load_config(self) -> None:
        """加載配置"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                self.logger.warning(f"Config file not found: {self.config_path}")
                await self._create_default_config()
                return

            with open(config_file, "r", encoding="utf - 8") as f:
                config_data = json.load(f)

            self.adapter_configs = {}
            for adapter_config in config_data.get("adapters", []):
                name = adapter_config["name"]
                if adapter_config.get("enabled", True):
                    self.adapter_configs[name] = adapter_config
                    self.logger.info(f"Loaded adapter config: {name}")
                else:
                    self.logger.info(f"Skipping disabled adapter: {name}")

        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            await self._create_default_config()

    async def _create_default_config(self) -> None:
        """創建默認配置"""
        try:
            config_dir = Path(self.config_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)

            default_config = {
                "adapters": [
                    {
                        "name": "yahoo_finance",
                        "enabled": True,
                        "priority": 1,
                        "config": {
                            "source_type": "yahoo_finance",
                            "source_path": "https://finance.yahoo.com",
                            "update_frequency": 60,
                            "max_retries": 3,
                            "timeout": 30,
                            "cache_enabled": True,
                            "cache_ttl": 300,
                            "quality_threshold": 0.8,
                        },
                    },
                    {
                        "name": "alpha_vantage",
                        "enabled": False,  # 需要API密鑰
                        "priority": 2,
                        "config": {
                            "source_type": "alpha_vantage",
                            "source_path": "https://www.alphavantage.co",
                            "api_key": "YOUR_API_KEY_HERE",
                            "update_frequency": 60,
                            "max_retries": 3,
                            "timeout": 30,
                            "cache_enabled": True,
                            "cache_ttl": 300,
                            "quality_threshold": 0.8,
                        },
                    },
                    {
                        "name": "binance_crypto",
                        "enabled": True,
                        "priority": 3,
                        "config": {
                            "source_type": "custom",
                            "source_path": "https://api.binance.com",
                            "exchange": "binance",
                            "sandbox": True,
                            "api_key": None,
                            "secret": None,
                            "update_frequency": 30,
                            "max_retries": 3,
                            "timeout": 30,
                            "cache_enabled": True,
                            "cache_ttl": 60,
                            "quality_threshold": 0.8,
                        },
                    },
                ]
            }

            with open(self.config_path, "w", encoding="utf - 8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Created default config: {self.config_path}")

        except Exception as e:
            self.logger.error(f"Error creating default config: {e}")

    async def _initialize_adapters(self) -> None:
        """初始化適配器"""
        try:
            for name, config in self.adapter_configs.items():
                try:
                    adapter = await self._create_adapter(name, config)
                    if adapter:
                        self.adapters[name] = adapter
                        self.logger.info(f"Initialized adapter: {name}")
                    else:
                        self.logger.warning(f"Failed to initialize adapter: {name}")

                except Exception as e:
                    self.logger.error(f"Error initializing adapter {name}: {e}")

        except Exception as e:
            self.logger.error(f"Error initializing adapters: {e}")

    async def _create_adapter(
        self, name: str, config: Dict
    ) -> Optional[BaseDataAdapter]:
        """創建適配器實例"""
        try:
            adapter_config = DataAdapterConfig(**config["config"])

            # 根據數據源類型創建相應的適配器
            if adapter_config.source_type == DataSourceType.YAHOO_FINANCE:
                return YahooFinanceAdapter(adapter_config)
            elif adapter_config.source_type == DataSourceType.ALPHA_VANTAGE:
                return AlphaVantageAdapter(adapter_config)
            elif adapter_config.source_type == DataSourceType.RAW_DATA:
                return RawDataAdapter(adapter_config)
            elif adapter_config.source_type == DataSourceType.HTTP_API:
                return HttpApiDataAdapter(adapter_config)
            elif adapter_config.source_type == DataSourceType.CUSTOM:
                # 檢查是否為加密貨幣適配器
                if config["config"].get("exchange"):
                    return CCXTCryptoAdapter(adapter_config)
                else:
                    self.logger.warning(f"Unknown custom adapter type: {name}")
                    return None
            else:
                self.logger.warning(
                    f"Unknown adapter type: {adapter_config.source_type}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error creating adapter {name}: {e}")
            return None

    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        preferred_adapter: Optional[str] = None,
    ) -> List[RealMarketData]:
        """獲取市場數據"""
        if not self._initialized:
            self.logger.error("Data service not initialized")
            return []

        try:
            # 如果指定了優先適配器，先嘗試該適配器
            if preferred_adapter and preferred_adapter in self.adapters:
                adapter = self.adapters[preferred_adapter]
                if await adapter.connect():
                    data = await adapter.get_market_data(symbol, start_date, end_date)
                    if data:
                        self.logger.info(
                            f"Got data from preferred adapter: {preferred_adapter}"
                        )
                        return data

            # 按優先級嘗試所有適配器
            sorted_adapters = sorted(
                self.adapters.items(),
                key=lambda x: self.adapter_configs[x[0]].get("priority", 999),
            )

            for adapter_name, adapter in sorted_adapters:
                try:
                    if await adapter.connect():
                        data = await adapter.get_market_data(
                            symbol, start_date, end_date
                        )
                        if data:
                            self.logger.info(f"Got data from adapter: {adapter_name}")
                            return data
                        else:
                            self.logger.debug(f"No data from adapter: {adapter_name}")
                    else:
                        self.logger.warning(
                            f"Failed to connect to adapter: {adapter_name}"
                        )

                except Exception as e:
                    self.logger.error(f"Error with adapter {adapter_name}: {e}")
                    continue

            self.logger.warning(f"No data found for symbol: {symbol}")
            return []

        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return []

    async def get_real_time_data(
        self, symbol: str, preferred_adapter: Optional[str] = None
    ) -> Optional[RealMarketData]:
        """獲取實時數據"""
        if not self._initialized:
            self.logger.error("Data service not initialized")
            return None

        try:
            # 如果指定了優先適配器，先嘗試該適配器
            if preferred_adapter and preferred_adapter in self.adapters:
                adapter = self.adapters[preferred_adapter]
                if await adapter.connect():
                    data = await adapter.get_real_time_data(symbol)
                    if data:
                        return data

            # 按優先級嘗試所有適配器
            sorted_adapters = sorted(
                self.adapters.items(),
                key=lambda x: self.adapter_configs[x[0]].get("priority", 999),
            )

            for adapter_name, adapter in sorted_adapters:
                try:
                    if await adapter.connect():
                        data = await adapter.get_real_time_data(symbol)
                        if data:
                            return data

                except Exception as e:
                    self.logger.error(f"Error with adapter {adapter_name}: {e}")
                    continue

            return None

        except Exception as e:
            self.logger.error(f"Error getting real - time data: {e}")
            return None

    async def get_multiple_symbols_data(
        self,
        symbols: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        preferred_adapter: Optional[str] = None,
    ) -> Dict[str, List[RealMarketData]]:
        """批量獲取多個標的數據"""
        try:
            # 並行獲取數據
            tasks = [
                self.get_market_data(symbol, start_date, end_date, preferred_adapter)
                for symbol in symbols
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            symbol_data = {}
            for symbol, result in zip(symbols, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error fetching data for {symbol}: {result}")
                    symbol_data[symbol] = []
                else:
                    symbol_data[symbol] = result

            successful_symbols = len([s for s, data in symbol_data.items() if data])
            self.logger.info(
                f"Successfully fetched data for {successful_symbols}/{len(symbols)} symbols"
            )

            return symbol_data

        except Exception as e:
            self.logger.error(f"Error fetching multiple symbols data: {e}")
            return {}

    async def search_symbols(self, query: str) -> List[Dict[str, Any]]:
        """搜索標的符號"""
        try:
            all_results = []

            # 從所有適配器搜索
            for adapter_name, adapter in self.adapters.items():
                try:
                    if await adapter.connect():
                        results = await adapter.search_symbols(query)
                        for result in results:
                            result["adapter"] = adapter_name
                        all_results.extend(results)

                except Exception as e:
                    self.logger.error(
                        f"Error searching with adapter {adapter_name}: {e}"
                    )
                    continue

            # 去重並排序
            unique_results = []
            seen_symbols = set()

            for result in all_results:
                symbol = result.get("symbol", "")
                if symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    unique_results.append(result)

            return unique_results[:50]  # 限制結果數量

        except Exception as e:
            self.logger.error(f"Error searching symbols: {e}")
            return []

    async def get_adapter_status(self) -> Dict[str, Any]:
        """獲取所有適配器狀態"""
        try:
            status = {}

            for adapter_name, adapter in self.adapters.items():
                try:
                    health_info = await adapter.health_check()
                    status[adapter_name] = {
                        "status": health_info.get("status", "unknown"),
                        "source_type": health_info.get("source_type", "unknown"),
                        "last_update": health_info.get("last_update"),
                        "cache_size": health_info.get("cache_size", 0),
                        "config": health_info.get("config", {}),
                    }
                except Exception as e:
                    status[adapter_name] = {"status": "error", "error": str(e)}

            return status

        except Exception as e:
            self.logger.error(f"Error getting adapter status: {e}")
            return {}

    async def validate_data_quality(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, DataValidationResult]:
        """驗證所有適配器的數據質量"""
        try:
            validation_results = {}

            for adapter_name, adapter in self.adapters.items():
                try:
                    if await adapter.connect():
                        data = await adapter.get_market_data(
                            symbol, start_date, end_date
                        )
                        if data:
                            validation_result = await adapter.validate_data(data)
                            validation_results[adapter_name] = validation_result
                        else:
                            validation_results[adapter_name] = DataValidationResult(
                                is_valid=False,
                                quality_score=0.0,
                                quality_level="unknown",
                                errors=["No data available"],
                                warnings=[],
                            )

                except Exception as e:
                    validation_results[adapter_name] = DataValidationResult(
                        is_valid=False,
                        quality_score=0.0,
                        quality_level="unknown",
                        errors=[f"Adapter error: {str(e)}"],
                        warnings=[],
                    )

            return validation_results

        except Exception as e:
            self.logger.error(f"Error validating data quality: {e}")
            return {}

    async def cleanup(self) -> None:
        """清理資源"""
        try:
            for adapter_name, adapter in self.adapters.items():
                try:
                    await adapter.disconnect()
                    self.logger.info(f"Disconnected adapter: {adapter_name}")
                except Exception as e:
                    self.logger.error(
                        f"Error disconnecting adapter {adapter_name}: {e}"
                    )

            self.adapters.clear()
            self.adapter_configs.clear()
            self._initialized = False

            self.logger.info("Data service cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def get_available_adapters(self) -> List[str]:
        """獲取可用的適配器列表"""
        return list(self.adapters.keys())

    def get_adapter_info(self, adapter_name: str) -> Optional[Dict]:
        """獲取適配器信息"""
        if adapter_name in self.adapter_configs:
            return self.adapter_configs[adapter_name]
        return None
