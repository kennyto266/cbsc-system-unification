#!/usr / bin / env python3
"""
HKMA貨幣基礎數據適配器
Hong Kong Monetary Authority Monetary Base API Adapter

專門用於獲取香港金管會貨幣基礎每日數據
API端點: https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base
"""

import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp
import pandas as pd
from pydantic import BaseModel, Field

from .base_adapter import (
    BaseDataAdapter,
    DataAdapterConfig,
    DataQuality,
    DataSourceType,
    DataValidationResult,
)


class HKMAMonetaryBaseConfig(DataAdapterConfig):
    """HKMA貨幣基礎數據適配器配置"""

    source_type: DataSourceType = Field(default=DataSourceType.HTTP_API)
    base_url: str = Field(
        default="https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics",
        description="HKMA API基礎URL",
    )
    endpoint: str = Field(
        default="daily - figures - monetary - base", description="貨幣基礎數據端點"
    )

    # 請求配置
    timeout: int = Field(default=30, description="請求超時時間(秒)")
    max_retries: int = Field(default=3, description="最大重試次數")
    retry_delay: float = Field(default=1.0, description="重試延遲(秒)")

    # 數據字段映射
    field_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "end_of_date": "date",
            "monetary_base": "monetary_base",
            "claims_on_banks": "claims_on_banks",
            "govt_bonds": "government_bonds",
            "exchange_fund_bills": "exchange_fund_bills",
            "exchange_fund_notes": "exchange_fund_notes",
            "other_liabilities": "other_liabilities",
            "total_outstanding": "total_outstanding",
        }
    )


class MonetaryBaseData(BaseModel):
    """貨幣基礎數據模型"""

    date: datetime = Field(..., description="數據日期")
    monetary_base: Optional[Decimal] = Field(None, description="貨幣基礎總額")
    claims_on_banks: Optional[Decimal] = Field(None, description="對銀行的債權")
    government_bonds: Optional[Decimal] = Field(None, description="政府債券")
    exchange_fund_bills: Optional[Decimal] = Field(None, description="外匯基金票據")
    exchange_fund_notes: Optional[Decimal] = Field(None, description="外匯基金債券")
    other_liabilities: Optional[Decimal] = Field(None, description="其他負債")
    total_outstanding: Optional[Decimal] = Field(None, description="未償還總額")
    source: str = Field(default="hkma_api", description="數據源")


class HKMAMonetaryBaseAdapter(BaseDataAdapter):
    """HKMA貨幣基礎數據適配器"""

    def __init__(self, config: HKMAMonetaryBaseConfig):
        super().__init__(config)
        self.config: HKMAMonetaryBaseConfig
        self.logger = logging.getLogger("hk_quant_system.hkma_monetary_base")
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """建立連接"""
        try:
            if self.session is None or self.session.closed:
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                self.session = aiohttp.ClientSession(
                    timeout=timeout, headers={"User - Agent": "HK - Quant - System / 1.0"}
                )

            # 測試連接
            test_url = urljoin(self.config.base_url, self.config.endpoint)
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    self.logger.info("HKMA API connection established successfully")
                    return True
                else:
                    self.logger.error(f"HKMA API test failed: HTTP {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to connect to HKMA API: {e}")
            return False

    async def disconnect(self) -> bool:
        """斷開連接"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
                self.logger.info("HKMA API connection closed")
            return True
        except Exception as e:
            self.logger.warning(f"Error closing HKMA connection: {e}")
            return False

    async def get_monetary_base_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 1000,
    ) -> List[MonetaryBaseData]:
        """
        獲取貨幣基礎數據

        Args:
            start_date: 開始日期
            end_date: 結束日期
            limit: 最大返回記錄數

        Returns:
            貨幣基礎數據列表
        """
        if not await self.connect():
            return []

        try:
            # 構建API URL
            api_url = urljoin(self.config.base_url, self.config.endpoint)

            # 添加參數
            params = {"pagesize": "100" if limit > 100 else str(limit), "page": "1"}

            # 如果指定了日期範圍，添加篩選條件
            if start_date:
                params["from"] = start_date.strftime("%d-%m-%Y")
            if end_date:
                params["to"] = end_date.strftime("%d-%m-%Y")

            self.logger.info(f"Fetching HKMA monetary base data from {api_url}")

            # 發送請求
            data = await self._fetch_with_retry(api_url, params)

            if not data:
                return []

            # 解析和轉換數據
            transformed_data = await self._transform_response(data)

            self._last_update = datetime.now()

            self.logger.info(
                f"Successfully fetched {len(transformed_data)} monetary base records"
            )
            return transformed_data

        except Exception as e:
            self.logger.error(f"Error fetching monetary base data: {e}")
            return []

    async def get_latest_monetary_base(self) -> Optional[MonetaryBaseData]:
        """獲取最新的貨幣基礎數據"""
        data = await self.get_monetary_base_data(limit=1)
        return data[0] if data else None

    async def get_monetary_base_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        獲取貨幣基礎統計數據

        Args:
            days: 統計天數

        Returns:
            統計數據字典
        """
        end_date = datetime.now().date()
        start_date = end_date - pd.Timedelta(days=days)

        data = await self.get_monetary_base_data(start_date, end_date)

        if not data:
            return {}

        # 提取數值進行統計
        monetary_base_values = [
            d.monetary_base for d in data if d.monetary_base is not None
        ]

        if not monetary_base_values:
            return {}

        values_float = [float(v) for v in monetary_base_values]

        return {
            "period_days": days,
            "data_points": len(monetary_base_values),
            "latest_value": values_float[-1] if values_float else None,
            "change_latest_vs_first": (
                values_float[-1] - values_float[0] if len(values_float) > 1 else 0
            ),
            "change_percent": (
                ((values_float[-1] / values_float[0]) - 1) * 100
                if len(values_float) > 1 and values_float[0] != 0
                else 0
            ),
            "average": sum(values_float) / len(values_float),
            "minimum": min(values_float),
            "maximum": max(values_float),
            "trend": (
                "increasing"
                if len(values_float) > 1 and values_float[-1] > values_float[0]
                else "decreasing" if len(values_float) > 1 else "stable"
            ),
        }

    async def _fetch_with_retry(
        self, url: str, params: Dict[str, str]
    ) -> Optional[Dict]:
        """帶重試的HTTP請求"""
        for attempt in range(self.config.max_retries + 1):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        self.logger.warning(
                            f"HTTP {response.status} on attempt {attempt + 1}"
                        )

            except Exception as e:
                self.logger.warning(f"Request failed on attempt {attempt + 1}: {e}")

            if attempt < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        return None

    async def _transform_response(self, raw_data: Dict) -> List[MonetaryBaseData]:
        """轉換API響應為標準格式"""
        try:
            # HKMA API通常返回 { "datas": { "records": [...] } } 格式
            records = []

            if "datas" in raw_data and isinstance(raw_data["datas"], dict):
                if "records" in raw_data["datas"]:
                    records = raw_data["datas"]["records"]
                else:
                    records = raw_data["datas"]
            elif "records" in raw_data:
                records = raw_data["records"]
            elif isinstance(raw_data, list):
                records = raw_data
            else:
                self.logger.warning("Unexpected API response format")
                return []

            transformed_data = []
            field_map = self.config.field_mapping

            for record in records:
                try:
                    # 解析日期
                    date_str = record.get("end_of_date") or record.get("date")
                    if not date_str:
                        continue

                    # HKMA API日期格式通常是 DD / MM / YYYY 或 YYYY - MM - DD
                    try:
                        if "/" in date_str:
                            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                        else:
                            date_obj = datetime.fromisoformat(
                                date_str.replace("Z", "+00:00")
                            )
                    except Exception:
                        self.logger.warning(f"Failed to parse date: {date_str}")
                        continue

                    # 提取數值字段
                    monetary_base = self._parse_decimal_field(record, "monetary_base")
                    claims_on_banks = self._parse_decimal_field(
                        record, "claims_on_banks"
                    )
                    government_bonds = self._parse_decimal_field(
                        record, "govt_bonds"
                    ) or self._parse_decimal_field(record, "government_bonds")
                    exchange_fund_bills = self._parse_decimal_field(
                        record, "exchange_fund_bills"
                    )
                    exchange_fund_notes = self._parse_decimal_field(
                        record, "exchange_fund_notes"
                    )
                    other_liabilities = self._parse_decimal_field(
                        record, "other_liabilities"
                    )
                    total_outstanding = self._parse_decimal_field(
                        record, "total_outstanding"
                    )

                    monetary_data = MonetaryBaseData(
                        date=date_obj,
                        monetary_base=monetary_base,
                        claims_on_banks=claims_on_banks,
                        government_bonds=government_bonds,
                        exchange_fund_bills=exchange_fund_bills,
                        exchange_fund_notes=exchange_fund_notes,
                        other_liabilities=other_liabilities,
                        total_outstanding=total_outstanding,
                        source="hkma_api",
                    )

                    transformed_data.append(monetary_data)

                except Exception as e:
                    self.logger.debug(f"Failed to transform record: {e}")
                    continue

            # 按日期排序
            transformed_data.sort(key=lambda x: x.date)
            return transformed_data

        except Exception as e:
            self.logger.error(f"Failed to transform response: {e}")
            return []

    def _parse_decimal_field(self, record: Dict, field_name: str) -> Optional[Decimal]:
        """解析數值字段"""
        try:
            value = record.get(field_name)
            if value is None or value == "":
                return None

            # 移除非數字字符（逗號、空格等）
            if isinstance(value, str):
                value = value.replace(",", "").replace(" ", "")

            return Decimal(str(value))

        except Exception:
            return None

    async def validate_data(self, data: List[MonetaryBaseData]) -> DataValidationResult:
        """驗證數據質量"""
        if not data:
            return DataValidationResult(
                is_valid=False,
                quality_score=0.0,
                quality_level=DataQuality.UNKNOWN,
                errors=["Empty data"],
                warnings=[],
            )

        # 檢查數據完整性
        errors = []
        warnings = []
        valid_records = 0

        for record in data:
            if record.monetary_base is None:
                warnings.append(f"Missing monetary_base value for {record.date}")
            else:
                valid_records += 1

            # 檢查數值合理性
            if record.monetary_base and record.monetary_base <= 0:
                errors.append(
                    f"Invalid monetary_base value: {record.monetary_base} for {record.date}"
                )

        # 計算質量分數
        total_records = len(data)
        completeness_score = valid_records / total_records if total_records > 0 else 0

        # 沒有錯誤且完整性 > 80% 視為高質量
        quality_score = completeness_score if not errors else completeness_score * 0.5

        return DataValidationResult(
            is_valid=len(errors) == 0,
            quality_score=quality_score,
            quality_level=self.get_quality_level(quality_score),
            errors=errors,
            warnings=warnings,
        )

    async def transform_data(self, raw_data: Any) -> List[Any]:
        """實現基類方法"""
        if isinstance(raw_data, dict):
            return await self._transform_response(raw_data)
        return []

    async def get_supported_symbols(self) -> List[str]:
        """HKMA貨幣基礎數據不需要股票代碼"""
        return ["HKD_MONETARY_BASE"]

    async def get_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        duration_days: int = 365,
    ) -> List[Any]:
        """實現基類方法"""
        if symbol != "HKD_MONETARY_BASE":
            return []

        if not start_date:
            end_date = datetime.now().date()
            start_date = end_date - pd.Timedelta(days=duration_days)

        return await self.get_monetary_base_data(start_date, end_date)
