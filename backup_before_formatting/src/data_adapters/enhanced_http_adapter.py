"""
增強版HTTP適配器

使用新的AsyncHTTPClient實現，整合了：
- 連接池管理
- 批量請求
- 重試機制
- Prometheus監控
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# 導入新AsyncHTTPClient
try:
    from src.core.async_http_client import AsyncHTTPClient
    from src.utils.http_utils import load_config
except ImportError:
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.async_http_client import AsyncHTTPClient
    from utils.http_utils import load_config

from .base_adapter import (
    BaseDataAdapter,
    DataAdapterConfig,
    DataQuality,
    DataSourceType,
    DataValidationResult,
    RealMarketData,
)


class EnhancedHttpApiAdapterConfig(DataAdapterConfig):
    """增強版HTTP API適配器配置"""

    source_type: DataSourceType = Field(default=DataSourceType.HTTP_API)
    source_path: str = Field(
        default="http://18.180.162.113:9191", description="基礎URL"
    )
    endpoint_symbol: str = Field(default="/inst / getInst", description="股票數據端點")
    api_key: Optional[str] = Field(None, description="API密鑰")
    api_key_header: Optional[str] = Field(None, description="API密鑰Header名")

    # HTTP客戶端配置
    http_max_connections: int = Field(default=1000, description="HTTP連接池大小")
    http_max_connections_per_host: int = Field(
        default=100, description="每主機連接限制"
    )
    http_timeout: int = Field(default=30, description="HTTP超時時間")
    http_max_retries: int = Field(default=3, description="最大重試次數")

    # 批量請求配置
    batch_size: int = Field(default=100, description="批量請求大小")
    batch_max_concurrent: int = Field(default=100, description="批量請求最大併發")

    # 字段映射
    json_field_map: Dict[str, str] = Field(
        default_factory=lambda: {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "timestamp": "timestamp",
        },
        description="JSON字段映射",
    )


class EnhancedHttpApiAdapter(BaseDataAdapter):
    """增強版HTTP API適配器"""

    def __init__(self, config: EnhancedHttpApiAdapterConfig):
        super().__init__(config)
        self.config: EnhancedHttpApiAdapterConfig
        self.logger = logging.getLogger("hk_quant_system.data_adapter.enhanced_http")
        self._http_client: Optional[AsyncHTTPClient] = None
        self._config_loaded = False

    async def _get_http_client(self) -> AsyncHTTPClient:
        """獲取或創建HTTP客戶端"""
        if self._http_client is None or self._http_client.session.closed:
            self._http_client = AsyncHTTPClient(
                max_connections=self.config.http_max_connections,
                max_connections_per_host=self.config.http_max_connections_per_host,
                timeout=self.config.http_timeout,
                max_retries=self.config.http_max_retries,
            )
            await self._http_client.create_session()

            if not self._config_loaded:
                self.logger.info(
                    "Enhanced HTTP adapter initialized with "
                    f"pool_size={self.config.http_max_connections}, "
                    f"per_host={self.config.http_max_connections_per_host}"
                )
                self._config_loaded = True

        return self._http_client

    async def connect(self) -> bool:
        """連接適配器"""
        try:
            await self._get_http_client()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect HTTP adapter: {e}")
            return False

    async def disconnect(self) -> bool:
        """斷開適配器"""
        try:
            if self._http_client:
                await self._http_client.close()
                self._http_client = None
            return True
        except Exception as e:
            self.logger.warning(f"Error closing HTTP adapter: {e}")
            return False

    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        duration_days: int = 365,
    ) -> List[RealMarketData]:
        """
        獲取單個股票市場數據

        Args:
            symbol: 股票代碼
            start_date: 開始日期（兼容性保留）
            end_date: 結束日期（兼容性保留）
            duration_days: 持續時間（天）

        Returns:
            市場數據列表
        """
        await self.connect()

        try:
            client = await self._get_http_client()

            # 構建URL和參數
            url = f"{self.config.source_path.rstrip('/')}/{self.config.endpoint_symbol.lstrip('/')}"
            params = {"symbol": symbol.lower(), "duration": duration_days}

            # 添加API密鑰（如果存在）
            headers = {}
            if self.config.api_key and self.config.api_key_header:
                headers[self.config.api_key_header] = self.config.api_key

            # 發送請求
            self.logger.debug(f"Fetching data for {symbol}")
            result = await client.get(url, params=params, headers=headers)

            if not result.get("success"):
                self.logger.warning(
                    f"Failed to fetch data for {symbol}: {result.get('error')}"
                )
                return []

            # 轉換數據
            raw_data = {
                "symbol": symbol,
                "data": result["data"],
                "duration": result.get("duration"),
                "response_time_ms": (
                    round(result.get("duration", 0) * 1000, 2)
                    if result.get("duration")
                    else None
                ),
            }

            transformed = await self.transform_data(raw_data)
            self._last_update = datetime.now()

            self.logger.info(
                f"Successfully fetched data for {symbol}, "
                f"records={len(transformed)}, "
                f"response_time={raw_data.get('response_time_ms')}ms"
            )

            return transformed

        except Exception as e:
            self.logger.error(f"Error fetching market data for {symbol}: {e}")
            return []

    async def get_batch_market_data(
        self,
        symbols: List[str],
        duration_days: int = 365,
    ) -> Dict[str, List[RealMarketData]]:
        """
        批量獲取市場數據 (US - 003)

        Args:
            symbols: 股票代碼列表
            duration_days: 持續時間（天）

        Returns:
            字典：{symbol: data_list}
        """
        await self.connect()

        try:
            client = await self._get_http_client()

            # 構建批量請求
            base_url = f"{self.config.source_path.rstrip('/')}/{self.config.endpoint_symbol.lstrip('/')}"

            requests = [
                {
                    "method": "GET",
                    "url": base_url,
                    "params": {"symbol": symbol.lower(), "duration": duration_days},
                    "headers": (
                        {self.config.api_key_header: self.config.api_key}
                        if self.config.api_key and self.config.api_key_header
                        else {}
                    ),
                }
                for symbol in symbols
            ]

            self.logger.info(f"Starting batch fetch for {len(symbols)} symbols")

            # 發送批量請求
            results = await client.batch_request(
                requests,
                max_concurrent=min(self.config.batch_max_concurrent, len(symbols)),
            )

            # 處理結果
            data_map: Dict[str, List[RealMarketData]] = {}
            success_count = 0

            for i, result in enumerate(results):
                symbol = symbols[i]

                if result.get("success"):
                    raw_data = {
                        "symbol": symbol,
                        "data": result["data"],
                        "duration": result.get("duration"),
                        "response_time_ms": (
                            round(result.get("duration", 0) * 1000, 2)
                            if result.get("duration")
                            else None
                        ),
                    }

                    try:
                        transformed = await self.transform_data(raw_data)
                        data_map[symbol] = transformed
                        success_count += 1

                        self.logger.debug(
                            f"Batch fetch {symbol}: {len(transformed)} records, "
                            f"{raw_data.get('response_time_ms')}ms"
                        )
                    except Exception as e:
                        self.logger.error(f"Transform data failed for {symbol}: {e}")
                        data_map[symbol] = []
                else:
                    self.logger.warning(
                        f"Batch fetch failed for {symbol}: {result.get('error')}"
                    )
                    data_map[symbol] = []

            self._last_update = datetime.now()

            self.logger.info(
                f"Batch fetch completed: {success_count}/{len(symbols)} successful"
            )

            return data_map

        except Exception as e:
            self.logger.error(f"Batch fetch error: {e}")
            return {symbol: [] for symbol in symbols}

    async def validate_data(self, data: List[RealMarketData]) -> DataValidationResult:
        """驗證數據質量"""
        if not data:
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level=DataQuality.UNKNOWN,
                errors=["Empty data"],
                warnings=[],
            )

        score = self.calculate_quality_score(data)
        level = self.get_quality_level(score)

        return DataValidationResult(
            is_valid=score >= float(self.config.quality_threshold),
            quality_score=score,
            quality_level=level,
            errors=[],
            warnings=[],
        )

    async def transform_data(self, raw_data: Any) -> List[RealMarketData]:
        """轉換原始數據為標準格式"""
        try:
            symbol = raw_data.get("symbol")
            payload = raw_data.get("data")

            # 適配API返回結構
            if (
                isinstance(payload, dict)
                and "data" in payload
                and isinstance(payload["data"], dict)
            ):
                payload = payload["data"]

            fm = self.config.json_field_map

            def extract_scalar(value: Any) -> Decimal:
                try:
                    if isinstance(value, dict) and value:
                        try:
                            last_key = sorted(value.keys())[-1]
                            return Decimal(str(value[last_key]))
                        except Exception:
                            return Decimal(str(list(value.values())[-1]))
                    if isinstance(value, list) and value:
                        return Decimal(str(value[-1]))
                    return Decimal(str(value if value is not None else 0))
                except Exception:
                    return Decimal("0")

            def extract_ts_from(value: Any) -> Optional[datetime]:
                try:
                    if isinstance(value, dict) and value:
                        try:
                            last_key = sorted(value.keys())[-1]
                            ts_value = value[last_key]
                        except Exception:
                            ts_value = list(value.values())[-1]
                    elif isinstance(value, list) and value:
                        ts_value = value[-1]
                    else:
                        ts_value = value

                    if isinstance(ts_value, (int, float)):
                        return datetime.fromtimestamp(ts_value)
                    elif isinstance(ts_value, str):
                        return datetime.fromisoformat(ts_value.replace("Z", "+00:00"))
                    else:
                        return None
                except Exception:
                    return None

            result: List[RealMarketData] = []

            if isinstance(payload, dict):
                for date_key, day_data in payload.items():
                    try:
                        open_price = extract_scalar(
                            day_data.get(fm.get("open", "open"))
                        )
                        high_price = extract_scalar(
                            day_data.get(fm.get("high", "high"))
                        )
                        low_price = extract_scalar(day_data.get(fm.get("low", "low")))
                        close_price = extract_scalar(
                            day_data.get(fm.get("close", "close"))
                        )
                        volume = extract_scalar(
                            day_data.get(fm.get("volume", "volume"))
                        )
                        timestamp = extract_ts_from(
                            day_data.get(fm.get("timestamp", "timestamp"))
                        )

                        result.append(
                            RealMarketData(
                                symbol=symbol,
                                timestamp=timestamp or datetime.now(),
                                open=open_price,
                                high=high_price,
                                low=low_price,
                                close=close_price,
                                volume=volume,
                                source="enhanced_http_api",
                            )
                        )
                    except Exception as e:
                        self.logger.debug(f"Transform error for {date_key}: {e}")
                        continue

            elif isinstance(payload, list):
                for item in payload:
                    try:
                        result.append(
                            RealMarketData(
                                symbol=symbol,
                                timestamp=extract_ts_from(item.get("timestamp"))
                                or datetime.now(),
                                open=extract_scalar(item.get("open")),
                                high=extract_scalar(item.get("high")),
                                low=extract_scalar(item.get("low")),
                                close=extract_scalar(item.get("close")),
                                volume=extract_scalar(item.get("volume")),
                                source="enhanced_http_api",
                            )
                        )
                    except Exception as e:
                        self.logger.debug(f"Transform error: {e}")
                        continue

            self.logger.debug(f"Transformed {len(result)} records for {symbol}")
            return result

        except Exception as e:
            self.logger.error(f"Transform data error: {e}")
            return []

    async def get_http_client_stats(self) -> Dict[str, Any]:
        """獲取HTTP客戶端統計信息"""
        if not self._http_client:
            return {"error": "HTTP client not initialized"}

        try:
            pool_status = await self._http_client.get_pool_status()
            metrics = self._http_client.get_metrics()

            return {
                "pool_status": pool_status,
                "metrics": metrics,
                "config": {
                    "max_connections": self.config.http_max_connections,
                    "max_connections_per_host": self.config.http_max_connections_per_host,
                    "timeout": self.config.http_timeout,
                    "max_retries": self.config.http_max_retries,
                },
            }
        except Exception as e:
            self.logger.error(f"Failed to get HTTP client stats: {e}")
            return {"error": str(e)}

    async def get_supported_symbols(self) -> List[str]:
        """獲取支持的股票代碼列表（示例）"""
        return [
            "0700.hk",  # 騰訊
            "0388.hk",  # 港交所
            "1398.hk",  # 工商銀行
            "0939.hk",  # 建設銀行
            "3988.hk",  # 中國銀行
            "2318.hk",  # 中國平安
            "1299.hk",  # 友邦保險
            "0941.hk",  # 中國移動
            "3690.hk",  # 美團
            "9988.hk",  # 阿里巴巴
            "9999.hk",  # 網易
            "2628.hk",  # 中國人壽
        ]


# 別名，方便使用
HttpAdapter = EnhancedHttpApiAdapter
AsyncHttpAdapter = EnhancedHttpApiAdapter
