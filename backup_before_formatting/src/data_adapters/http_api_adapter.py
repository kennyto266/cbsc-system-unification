"""
HTTP API 数据适配器

支持：
- 基于 HTTP GET 拉取行情（如：http://host:port / getStockBySymbol?symbol=XXX）
- 全局频率限制与每符号频率限制
- 简单重试与超时控制
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import AnyHttpUrl, BaseModel, Field

from .base_adapter import (
    BaseDataAdapter,
    DataAdapterConfig,
    DataQuality,
    DataSourceType,
    DataValidationResult,
    RealMarketData,
)


class HttpApiAdapterConfig(DataAdapterConfig):
    """HTTP API 适配器配置"""

    source_type: DataSourceType = Field(default=DataSourceType.HTTP_API)
    source_path: str = Field(
        ..., description="基础URL，例如：http://18.180.162.113:9888"
    )
    endpoint_symbol: str = Field(
        "/getStockBySymbol", description="按符号取数的相对路径"
    )
    api_key: Optional[str] = Field(None, description="可选：API Key")
    api_key_header: Optional[str] = Field(
        None, description="可选：API Key 所在Header名"
    )
    default_params: Dict[str, Any] = Field(
        default_factory=dict, description="可选：默认查询参数"
    )

    # 频率限制
    rate_limit_rps: float = Field(1.0, gt=0, description="全局每秒最大请求数")
    per_symbol_min_interval_sec: float = Field(
        1.0, gt=0, description="每个symbol最小请求间隔（秒）"
    )

    # 字段映射（根据返回JSON字段名做映射）
    json_field_map: Dict[str, str] = Field(
        default_factory=lambda: {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "timestamp": "timestamp",
        },
        description="返回JSON字段与标准字段映射",
    )


class HttpApiDataAdapter(BaseDataAdapter):
    """HTTP API 数据适配器实现"""

    def __init__(self, config: HttpApiAdapterConfig):
        super().__init__(config)
        self.config: HttpApiAdapterConfig
        self.logger = logging.getLogger("hk_quant_system.data_adapter.http_api")
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_request_time: Optional[datetime] = None
        self._symbol_last_ts: Dict[str, datetime] = {}

    async def connect(self) -> bool:
        try:
            if self._session is None:
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                self._session = aiohttp.ClientSession(timeout=timeout)
            return True
        except Exception as e:
            self.logger.error(f"HTTP session init failed: {e}")
            return False

    async def disconnect(self) -> bool:
        try:
            if self._session:
                await self._session.close()
                self._session = None
            return True
        except Exception as e:
            self.logger.warning(f"HTTP session close error: {e}")
            return False

    async def _apply_rate_limit_global(self) -> None:
        if self._last_request_time is None:
            return
        min_interval = 1.0 / max(self.config.rate_limit_rps, 1e-6)
        elapsed = (datetime.now() - self._last_request_time).total_seconds()
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

    async def _apply_rate_limit_symbol(self, symbol: str) -> None:
        last_ts = self._symbol_last_ts.get(symbol)
        if last_ts is None:
            return
        elapsed = (datetime.now() - last_ts).total_seconds()
        if elapsed < self.config.per_symbol_min_interval_sec:
            await asyncio.sleep(self.config.per_symbol_min_interval_sec - elapsed)

    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[RealMarketData]:
        await self.connect()

        try:
            await self._apply_rate_limit_global()
            await self._apply_rate_limit_symbol(symbol)

            base = self.config.source_path.rstrip("/")
            endpoint = self.config.endpoint_symbol.lstrip("/")
            url = f"{base}/{endpoint}"

            headers: Dict[str, str] = {}
            if self.config.api_key and self.config.api_key_header:
                headers[self.config.api_key_header] = self.config.api_key

            params = dict(self.config.default_params)
            params.update({"symbol": symbol})

            retries = max(1, self.config.max_retries)
            last_err: Optional[Exception] = None
            for _ in range(retries):
                try:
                    assert self._session is not None
                    async with self._session.get(
                        url, params=params, headers=headers
                    ) as resp:
                        text = await resp.text()
                        if resp.status != 200:
                            raise RuntimeError(f"HTTP {resp.status}: {text[:200]}")
                        data = await resp.json(content_type=None)

                    self._last_request_time = datetime.now()
                    self._symbol_last_ts[symbol] = self._last_request_time

                    transformed = await self.transform_data(
                        {"symbol": symbol, "data": data}
                    )
                    self._last_update = datetime.now()
                    return transformed
                except Exception as e:
                    last_err = e
                    await asyncio.sleep(0.5)

            raise last_err or RuntimeError("HTTP request failed")
        except Exception as e:
            self.logger.warning(f"get_market_data error for {symbol}: {e}")
            return []

    async def validate_data(self, data: List[RealMarketData]) -> DataValidationResult:
        if not data:
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level=DataQuality.UNKNOWN,
                errors=["empty data"],
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
        try:
            symbol = raw_data.get("symbol")
            payload = raw_data.get("data")

            # 适配 japan_stock_api_test 返回的结构：可能是 { ... } 或 {"data": {...}}
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
                        last_key = sorted(value.keys())[-1]
                        return datetime.fromisoformat(str(last_key))
                except Exception:
                    return None
                return None

            ts = None
            ts_field = payload.get(fm.get("timestamp", "timestamp"))
            if isinstance(ts_field, str):
                try:
                    ts = datetime.fromisoformat(ts_field)
                except Exception:
                    ts = None
            if ts is None:
                for key in [
                    fm.get("close", "close"),
                    fm.get("open", "open"),
                    fm.get("high", "high"),
                    fm.get("low", "low"),
                ]:
                    if key in payload:
                        ts = extract_ts_from(payload.get(key))
                        if ts is not None:
                            break
            # 若 payload 为时间序列（dict of timestamp->value），则展开为多条 RealMarketData
            open_map = payload.get(fm.get("open", "open"))
            high_map = payload.get(fm.get("high", "high"))
            low_map = payload.get(fm.get("low", "low"))
            close_map = payload.get(fm.get("close", "close"))
            vol_map = payload.get(fm.get("volume", "volume"))

            if isinstance(close_map, dict) or isinstance(open_map, dict):
                # 选择关键字段集合（优先使用 close 的键集合）
                keys = None
                for m in [close_map, open_map, high_map, low_map]:
                    if isinstance(m, dict) and m:
                        keys = sorted(m.keys())
                        break
                if not keys:
                    keys = []

                records: List[RealMarketData] = []
                for k in keys:
                    try:
                        t = None
                        try:
                            t = datetime.fromisoformat(str(k))
                        except Exception:
                            t = ts or datetime.now()

                        item = RealMarketData(
                            symbol=symbol,
                            timestamp=t,
                            open_price=extract_scalar(
                                open_map.get(k)
                                if isinstance(open_map, dict)
                                else open_map
                            ),
                            high_price=extract_scalar(
                                high_map.get(k)
                                if isinstance(high_map, dict)
                                else high_map
                            ),
                            low_price=extract_scalar(
                                low_map.get(k) if isinstance(low_map, dict) else low_map
                            ),
                            close_price=extract_scalar(
                                close_map.get(k)
                                if isinstance(close_map, dict)
                                else close_map
                            ),
                            volume=int(
                                extract_scalar(
                                    vol_map.get(k)
                                    if isinstance(vol_map, dict)
                                    else vol_map
                                )
                            ),
                            market_cap=None,
                            pe_ratio=None,
                            data_source=str(self.config.source_type),
                            quality_score=1.0,
                        )
                        records.append(item)
                    except Exception:
                        continue

                # 过滤掉不完整的记录
                records = [
                    r
                    for r in records
                    if r.open_price and r.high_price and r.low_price and r.close_price
                ]
                return records[:1000]  # 安全上限，避免极端长序列

            # 否则回退为单条快照
            if ts is None:
                ts = datetime.now()

            item = RealMarketData(
                symbol=symbol,
                timestamp=ts,
                open_price=extract_scalar(payload.get(fm.get("open", "open"), 0)),
                high_price=extract_scalar(payload.get(fm.get("high", "high"), 0)),
                low_price=extract_scalar(payload.get(fm.get("low", "low"), 0)),
                close_price=extract_scalar(payload.get(fm.get("close", "close"), 0)),
                volume=int(extract_scalar(payload.get(fm.get("volume", "volume"), 0))),
                market_cap=None,
                pe_ratio=None,
                data_source=str(self.config.source_type),
                quality_score=1.0,
            )
            return [item]
        except Exception as e:
            self.logger.warning(f"transform_data failed: {e}")
            return []
