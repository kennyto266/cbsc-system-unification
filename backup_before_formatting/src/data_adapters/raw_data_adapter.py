"""
黑人RAW DATA数据适配器

集成黑人RAW DATA项目的数据格式，提供数据读取、转换和验证功能。
"""

import asyncio
import logging
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from pydantic import Field

from .base_adapter import (
    BaseDataAdapter,
    DataAdapterConfig,
    DataQuality,
    DataSourceType,
    DataValidationResult,
    RealMarketData,
)


class RawDataAdapterConfig(DataAdapterConfig):
    """黑人RAW DATA适配器配置"""

    source_type: DataSourceType = DataSourceType.RAW_DATA
    source_path: str = Field(..., description="数据源路径")
    data_directory: str = Field(..., description="数据目录路径")
    file_pattern: str = Field("*.csv", description="数据文件模式")
    encoding: str = Field("utf - 8", description="文件编码")
    delimiter: str = Field(",", description="分隔符")
    date_column: str = Field("date", description="日期列名")
    symbol_column: str = Field("symbol", description="股票代码列名")
    price_columns: Dict[str, str] = Field(
        default_factory=lambda: {
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        },
        description="价格列映射",
    )
    market_cap_column: Optional[str] = Field(None, description="市值列名")
    pe_ratio_column: Optional[str] = Field(None, description="市盈率列名")

    class Config:
        use_enum_values = True


class RawDataAdapter(BaseDataAdapter):
    """黑人RAW DATA数据适配器"""

    def __init__(self, config: RawDataAdapterConfig):
        super().__init__(config)
        self.raw_config = config
        self._data_files: Dict[str, str] = {}
        self._file_cache: Dict[str, pd.DataFrame] = {}

    async def connect(self) -> bool:
        """连接到数据源（扫描数据文件）"""
        try:
            self.logger.info(
                f"Connecting to RAW DATA source: {self.raw_config.data_directory}"
            )

            data_path = Path(self.raw_config.data_directory)
            if not data_path.exists():
                self.logger.error(f"Data directory not found: {data_path}")
                return False

            # 扫描数据文件
            await self._scan_data_files()

            self.logger.info(f"Found {len(self._data_files)} data files")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to RAW DATA source: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开数据源连接"""
        try:
            self._data_files.clear()
            self._file_cache.clear()
            self.clear_cache()
            self.logger.info("Disconnected from RAW DATA source")
            return True
        except Exception as e:
            self.logger.error(f"Failed to disconnect: {e}")
            return False

    async def _scan_data_files(self) -> None:
        """扫描数据文件"""
        data_path = Path(self.raw_config.data_directory)

        for file_path in data_path.glob(self.raw_config.file_pattern):
            try:
                # 尝试读取文件头部来确定股票代码
                df = pd.read_csv(
                    file_path,
                    encoding=self.raw_config.encoding,
                    delimiter=self.raw_config.delimiter,
                    nrows=1,
                )

                if self.raw_config.symbol_column in df.columns:
                    symbol = df[self.raw_config.symbol_column].iloc[0]
                    self._data_files[str(symbol)] = str(file_path)
                    self.logger.debug(f"Found data file for {symbol}: {file_path}")

            except Exception as e:
                self.logger.warning(f"Failed to scan file {file_path}: {e}")

    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[RealMarketData]:
        """获取市场数据"""
        try:
            # 检查缓存
            cache_key = self.get_cache_key(symbol, start_date, end_date)
            cached_data = self.get_cache(cache_key)
            if cached_data:
                self.logger.debug(f"Returning cached data for {symbol}")
                return cached_data

            # 获取数据文件路径
            if symbol not in self._data_files:
                self.logger.error(f"No data file found for symbol: {symbol}")
                return []

            file_path = self._data_files[symbol]

            # 读取数据文件
            df = await self._read_data_file(file_path)
            if df is None or df.empty:
                return []

            # 转换数据
            market_data = await self._convert_to_market_data(
                df, symbol, start_date, end_date
            )

            # 缓存数据
            self.set_cache(cache_key, market_data)

            self.logger.info(f"Retrieved {len(market_data)} records for {symbol}")
            return market_data

        except Exception as e:
            self.logger.error(f"Failed to get market data for {symbol}: {e}")
            return []

    async def _read_data_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """读取数据文件"""
        try:
            # 检查文件缓存
            if file_path in self._file_cache:
                return self._file_cache[file_path]

            # 读取CSV文件
            df = pd.read_csv(
                file_path,
                encoding=self.raw_config.encoding,
                delimiter=self.raw_config.delimiter,
                parse_dates=[self.raw_config.date_column],
            )

            # 验证必需的列
            required_columns = [
                self.raw_config.date_column,
                self.raw_config.symbol_column,
            ] + list(self.raw_config.price_columns.values())

            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Missing required columns: {missing_columns}")
                return None

            # 缓存文件数据
            self._file_cache[file_path] = df

            return df

        except Exception as e:
            self.logger.error(f"Failed to read data file {file_path}: {e}")
            return None

    async def _convert_to_market_data(
        self,
        df: pd.DataFrame,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[RealMarketData]:
        """转换数据为市场数据格式"""
        try:
            market_data_list = []

            # 过滤日期范围
            if start_date:
                df = df[df[self.raw_config.date_column].dt.date >= start_date]
            if end_date:
                df = df[df[self.raw_config.date_column].dt.date <= end_date]

            # 按日期排序
            df = df.sort_values(self.raw_config.date_column)

            for _, row in df.iterrows():
                try:
                    # 提取价格数据
                    open_price = Decimal(
                        str(row[self.raw_config.price_columns["open"]])
                    )
                    high_price = Decimal(
                        str(row[self.raw_config.price_columns["high"]])
                    )
                    low_price = Decimal(str(row[self.raw_config.price_columns["low"]]))
                    close_price = Decimal(
                        str(row[self.raw_config.price_columns["close"]])
                    )
                    volume = int(row[self.raw_config.price_columns["volume"]])

                    # 提取可选数据
                    market_cap = None
                    if (
                        self.raw_config.market_cap_column
                        and self.raw_config.market_cap_column in row
                        and pd.notna(row[self.raw_config.market_cap_column])
                    ):
                        market_cap = Decimal(
                            str(row[self.raw_config.market_cap_column])
                        )

                    pe_ratio = None
                    if (
                        self.raw_config.pe_ratio_column
                        and self.raw_config.pe_ratio_column in row
                        and pd.notna(row[self.raw_config.pe_ratio_column])
                    ):
                        pe_ratio = Decimal(str(row[self.raw_config.pe_ratio_column]))

                    # 计算数据质量评分
                    quality_score = self._calculate_row_quality(row)

                    market_data = RealMarketData(
                        symbol=symbol,
                        timestamp=row[self.raw_config.date_column],
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        close_price=close_price,
                        volume=volume,
                        market_cap=market_cap,
                        pe_ratio=pe_ratio,
                        data_source=self.raw_config.source_type,
                        quality_score=quality_score,
                    )

                    market_data_list.append(market_data)

                except Exception as e:
                    self.logger.warning(f"Failed to convert row for {symbol}: {e}")
                    continue

            return market_data_list

        except Exception as e:
            self.logger.error(f"Failed to convert data for {symbol}: {e}")
            return []

    def _calculate_row_quality(self, row: pd.Series) -> float:
        """计算单行数据质量评分"""
        score = 1.0

        # 检查价格数据完整性
        price_columns = list(self.raw_config.price_columns.values())
        missing_prices = sum(1 for col in price_columns if pd.isna(row[col]))
        if missing_prices > 0:
            score -= 0.3 * (missing_prices / len(price_columns))

        # 检查价格合理性
        try:
            if not pd.isna(row[self.raw_config.price_columns["high"]]) and not pd.isna(
                row[self.raw_config.price_columns["low"]]
            ):
                if (
                    row[self.raw_config.price_columns["high"]]
                    < row[self.raw_config.price_columns["low"]]
                ):
                    score -= 0.5
        except Exception:
            score -= 0.2

        # 检查成交量
        volume_col = self.raw_config.price_columns["volume"]
        if pd.isna(row[volume_col]) or row[volume_col] <= 0:
            score -= 0.2

        return max(0.0, score)

    async def validate_data(self, data: List[RealMarketData]) -> DataValidationResult:
        """验证数据质量"""
        try:
            if not data:
                return DataValidationResult(
                    is_valid=False,
                    quality_score=0.0,
                    quality_level=DataQuality.UNKNOWN,
                    errors=["No data provided"],
                    warnings=[],
                )

            errors = []
            warnings = []
            total_score = 0.0

            for item in data:
                # 检查价格一致性
                if item.high_price < item.low_price:
                    errors.append(
                        f"High price < low price for {item.symbol} at {item.timestamp}"
                    )

                if (
                    item.open_price < item.low_price
                    or item.open_price > item.high_price
                ):
                    warnings.append(
                        f"Open price out of range for {item.symbol} at {item.timestamp}"
                    )

                if (
                    item.close_price < item.low_price
                    or item.close_price > item.high_price
                ):
                    warnings.append(
                        f"Close price out of range for {item.symbol} at {item.timestamp}"
                    )

                # 检查成交量
                if item.volume <= 0:
                    warnings.append(
                        f"Zero or negative volume for {item.symbol} at {item.timestamp}"
                    )

                # 检查时间戳
                if item.timestamp > datetime.now():
                    warnings.append(
                        f"Future timestamp for {item.symbol} at {item.timestamp}"
                    )

                total_score += item.quality_score

            avg_score = total_score / len(data)
            quality_level = self.get_quality_level(avg_score)
            is_valid = avg_score >= self.config.quality_threshold and len(errors) == 0

            return DataValidationResult(
                is_valid=is_valid,
                quality_score=avg_score,
                quality_level=quality_level,
                errors=errors,
                warnings=warnings,
                metadata={
                    "total_records": len(data),
                    "validation_timestamp": datetime.now(),
                    "data_source": self.raw_config.source_type,
                },
            )

        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level=DataQuality.UNKNOWN,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
            )

    async def transform_data(self, raw_data: Any) -> List[RealMarketData]:
        """转换原始数据为标准格式"""
        # 这个方法主要用于处理其他格式的原始数据
        # 对于CSV文件，我们已经在get_market_data中处理了转换
        if isinstance(raw_data, list):
            return raw_data
        elif isinstance(raw_data, pd.DataFrame):
            # 如果传入的是DataFrame，进行转换
            symbol = "unknown"
            if not raw_data.empty and self.raw_config.symbol_column in raw_data.columns:
                symbol = raw_data[self.raw_config.symbol_column].iloc[0]

            return await self._convert_to_market_data(raw_data, symbol)
        else:
            self.logger.warning(f"Unsupported raw data type: {type(raw_data)}")
            return []

    async def get_available_symbols(self) -> List[str]:
        """获取可用的股票代码列表"""
        return list(self._data_files.keys())

    async def refresh_data_files(self) -> bool:
        """刷新数据文件列表"""
        try:
            self._data_files.clear()
            self._file_cache.clear()
            await self._scan_data_files()
            self.logger.info(
                f"Refreshed data files, found {len(self._data_files)} symbols"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to refresh data files: {e}")
            return False
