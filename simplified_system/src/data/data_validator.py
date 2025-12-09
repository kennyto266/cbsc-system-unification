#!/usr / bin / env python3
"""
Simplified System - Real Data Validator
简化系统 - 真实数据验证器

验证数据源的真实性和质量，确保所有数据都来自经过验证的真实API端点。
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器"""

    def __init__(self):
        """初始化数据验证器"""
        self.validation_results = {}
        self.data_quality_scores = {}

        # 定义已验证的真实数据源
        self.verified_sources = {
            "stock_api": {
                "url": "http://18.180.162.113:9191",
                "endpoint": "/inst / getInst",
                "description": "香港股票数据API",
            },
            "hkma_hibor": {
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / hk - interbank - ir - daily",
                "description": "香港金融管理局HIBOR利率",
            },
            "hkma_exchange_rate": {
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / monthly - statistical - bulletin / er - ir / er - eeri - daily",
                "description": "香港金融管理局汇率数据",
            },
            "hkma_monetary_base": {
                "url": "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base",
                "description": "香港金融管理局货币基础数据",
            },
        }

    def validate_stock_data(self, symbol: str = "0700.hk") -> Dict[str, Any]:
        """
        验证股票数据

        Args:
            symbol: 股票代码

        Returns:
            验证结果字典
        """
        logger.info(f"Validating stock data for {symbol}")

        try:
            stock_url = f"{self.verified_sources['stock_api']['url']}/inst / getInst"
            params = {"symbol": symbol.lower(), "duration": 365}

            response = requests.get(stock_url, params = params, timeout = 30)
            response.raise_for_status()

            data = response.json()

            # 验证数据格式
            validation_result = self._validate_stock_data_format(data, symbol)

            if validation_result["is_valid"]:
                # 数据质量评分
                quality_score = self._calculate_stock_data_quality(data, symbol)
                validation_result["quality_score"] = quality_score
                logger.info(
                    f"Stock data validation PASSED for {symbol}, quality: {quality_score:.2f}"
                )
            else:
                logger.error(f"Stock data validation FAILED for {symbol}")

            self.validation_results[f"stock_{symbol}"] = validation_result
            return validation_result

        except Exception as e:
            logger.error(f"Error validating stock data for {symbol}: {e}")
            return {
                "source": "stock_api",
                "symbol": symbol,
                "is_valid": False,
                "error": str(e),
                "quality_score": 0.0,
            }

    def validate_government_data(self) -> Dict[str, Any]:
        """
        验证政府数据源

        Returns:
            验证结果字典
        """
        logger.info("Validating government data sources")

        results = {}

        for source_key, source_info in self.verified_sources.items():
            if source_key == "stock_api":
                continue

            try:
                result = self._validate_government_endpoint(source_key, source_info)
                results[source_key] = result
                logger.info(f"Government data {source_key}: {result['is_valid']}")

            except Exception as e:
                logger.error(f"Error validating {source_key}: {e}")
                results[source_key] = {
                    "source": source_key,
                    "url": source_info["url"],
                    "is_valid": False,
                    "error": str(e),
                    "quality_score": 0.0,
                }

        self.validation_results["government_data"] = results
        return results

    def _validate_government_endpoint(
        self, source_key: str, source_info: Dict
    ) -> Dict[str, Any]:
        """
        验证政府数据端点

        Args:
            source_key: 数据源键
            source_info: 数据源信息

        Returns:
            验证结果
        """
        try:
            params = {}
            if source_key == "hkma_hibor":
                params = {"segment": "hibor.fixing"}

            response = requests.get(source_info["url"], params = params, timeout = 30)
            response.raise_for_status()

            data = response.json()

            # 验证HKMA API响应格式
            records = self._parse_hkma_response(data)

            if records:
                # 数据质量评分
                quality_score = self._calculate_government_data_quality(
                    records, source_key
                )
                return {
                    "source": source_key,
                    "url": source_info["url"],
                    "is_valid": True,
                    "record_count": len(records),
                    "quality_score": quality_score,
                    "latest_record": records[-1] if records else None,
                }
            else:
                return {
                    "source": source_key,
                    "url": source_info["url"],
                    "is_valid": False,
                    "error": "No valid records found",
                    "quality_score": 0.0,
                }

        except Exception as e:
            return {
                "source": source_key,
                "url": source_info["url"],
                "is_valid": False,
                "error": str(e),
                "quality_score": 0.0,
            }

    def _parse_hkma_response(self, data: Dict) -> List[Dict]:
        """
        解析HKMA API响应

        Args:
            data: API响应数据

        Returns:
            记录列表
        """
        records = []

        try:
            # HKMA API可能返回不同的格式
            if "result" in data and "records" in data["result"]:
                records = data["result"]["records"]
            elif "datas" in data and "records" in data["datas"]:
                records = data["datas"]["records"]
            elif "records" in data:
                records = data["records"]

        except Exception as e:
            logger.error(f"Error parsing HKMA response: {e}")

        return records

    def _validate_stock_data_format(self, data: Dict, symbol: str) -> Dict[str, Any]:
        """
        验证股票数据格式

        Args:
            data: API响应数据
            symbol: 股票代码

        Returns:
            验证结果
        """
        validation_result = {
            "source": "stock_api",
            "symbol": symbol,
            "is_valid": False,
            "issues": [],
        }

        try:
            # 检查基本结构
            if not isinstance(data, dict):
                validation_result["issues"].append("Response is not a dictionary")
                return validation_result

            if "data" not in data:
                validation_result["issues"].append("Missing 'data' field in response")
                return validation_result

            if "close" not in data["data"]:
                validation_result["issues"].append("Missing 'close' price data")
                return validation_result

            close_data = data["data"]["close"]
            if not isinstance(close_data, dict) or len(close_data) == 0:
                validation_result["issues"].append("Empty or invalid close price data")
                return validation_result

            # 检查价格数据合理性
            prices = list(close_data.values())
            numeric_prices = []

            for price in prices:
                try:
                    numeric_price = float(price)
                    if numeric_price > 0:  # 价格必须为正数
                        numeric_prices.append(numeric_price)
                except (ValueError, TypeError):
                    validation_result["issues"].append(f"Invalid price value: {price}")

            if len(numeric_prices) < 10:
                validation_result["issues"].append(
                    "Insufficient price data (less than 10 records)"
                )

            # 检查价格范围合理性 (港股通常在1 - 10000范围内)
            min_price = min(numeric_prices) if numeric_prices else 0
            max_price = max(numeric_prices) if numeric_prices else 0

            if min_price <= 0 or max_price > 100000:
                validation_result["issues"].append(
                    f"Price range suspicious: {min_price:.2f} - {max_price:.2f}"
                )

            # 如果没有问题，标记为有效
            if not validation_result["issues"]:
                validation_result["is_valid"] = True
                validation_result["record_count"] = len(numeric_prices)
                validation_result["price_range"] = f"{min_price:.2f} - {max_price:.2f}"

        except Exception as e:
            validation_result["issues"].append(f"Validation error: {str(e)}")

        return validation_result

    def _calculate_stock_data_quality(self, data: Dict, symbol: str) -> float:
        """
        计算股票数据质量评分

        Args:
            data: 股票数据
            symbol: 股票代码

        Returns:
            质量评分 (0.0 - 1.0)
        """
        try:
            close_data = data["data"]["close"]
            prices = [float(p) for p in close_data.values() if p > 0]

            if not prices:
                return 0.0

            quality_factors = []

            # 数据完整性 (记录数量)
            record_count = len(prices)
            completeness_score = min(record_count / 250, 1.0)  # 假设250条记录为满分
            quality_factors.append(completeness_score)

            # 数据时效性 (最新记录日期)
            dates = list(close_data.keys())
            if dates:
                latest_date = datetime.fromisoformat(dates[-1].replace("Z", "+00:00"))
                days_old = (datetime.now(latest_date.tzinfo) - latest_date).days
                timeliness_score = max(0, 1 - days_old / 30)  # 30天内为满分
                quality_factors.append(timeliness_score)

            # 数据一致性 (价格变化合理性)
            if len(prices) > 1:
                price_changes = [
                    abs(prices[i] - prices[i - 1]) / prices[i - 1]
                    for i in range(1, len(prices))
                ]
                avg_change = np.mean(price_changes)
                # 日均变化不应超过50%
                consistency_score = max(0, 1 - avg_change / 0.5)
                quality_factors.append(consistency_score)

            return np.mean(quality_factors)

        except Exception as e:
            logger.error(f"Error calculating stock data quality: {e}")
            return 0.0

    def _calculate_government_data_quality(
        self, records: List[Dict], source_key: str
    ) -> float:
        """
        计算政府数据质量评分

        Args:
            records: 数据记录
            source_key: 数据源键

        Returns:
            质量评分 (0.0 - 1.0)
        """
        try:
            if not records:
                return 0.0

            quality_factors = []

            # 数据完整性
            record_count = len(records)
            completeness_score = min(record_count / 30, 1.0)  # 30条记录为满分
            quality_factors.append(completeness_score)

            # 数据时效性
            if records and "end_of_day" in records[0]:
                latest_date = datetime.fromisoformat(
                    records[0]["end_of_day"].replace("Z", "+00:00")
                )
                days_old = (datetime.now(latest_date.tzinfo) - latest_date).days
                timeliness_score = max(0, 1 - days_old / 30)
                quality_factors.append(timeliness_score)

            # 数据一致性 (根据数据源类型检查)
            if source_key == "hkma_hibor":
                consistency_score = self._validate_hibor_consistency(records)
                quality_factors.append(consistency_score)

            return np.mean(quality_factors)

        except Exception as e:
            logger.error(f"Error calculating government data quality: {e}")
            return 0.0

    def _validate_hibor_consistency(self, records: List[Dict]) -> float:
        """验证HIBOR数据一致性"""
        try:
            valid_rates = 0
            total_rates = 0

            for record in records:
                for key, value in record.items():
                    if "ir_" in key.lower() and isinstance(value, (int, float)):
                        total_rates += 1
                        # HIBOR利率通常在0 - 20%之间
                        if 0 <= value <= 20:
                            valid_rates += 1

            return valid_rates / total_rates if total_rates > 0 else 1.0

        except Exception:
            return 1.0

    def generate_validation_report(self) -> Dict[str, Any]:
        """
        生成验证报告

        Returns:
            验证报告
        """
        report = {
            "validation_time": datetime.now().isoformat(),
            "overall_status": "unknown",
            "summary": {
                "total_sources": len(self.verified_sources),
                "valid_sources": 0,
                "invalid_sources": 0,
                "average_quality_score": 0.0,
            },
            "details": self.validation_results,
            "recommendations": [],
        }

        # 统计有效数据源
        valid_count = 0
        total_quality = 0.0

        for source_key, source_info in self.verified_sources.items():
            if source_key == "stock_api":
                # 检查股票数据验证结果
                for result_key, result in self.validation_results.items():
                    if result_key.startswith("stock_") and result.get("is_valid"):
                        valid_count += 1
                        total_quality += result.get("quality_score", 0)
            elif f"government_data" in self.validation_results:
                gov_results = self.validation_results["government_data"]
                if source_key in gov_results and gov_results[source_key].get(
                    "is_valid"
                ):
                    valid_count += 1
                    total_quality += gov_results[source_key].get("quality_score", 0)

        report["summary"]["valid_sources"] = valid_count
        report["summary"]["invalid_sources"] = len(self.verified_sources) - valid_count
        report["summary"]["average_quality_score"] = (
            total_quality / valid_count if valid_count > 0 else 0.0
        )

        # 总体状态
        if valid_count == len(self.verified_sources):
            report["overall_status"] = "all_valid"
        elif valid_count > 0:
            report["overall_status"] = "partially_valid"
        else:
            report["overall_status"] = "all_invalid"

        # 生成建议
        if report["summary"]["average_quality_score"] < 0.7:
            report["recommendations"].append("数据质量较低，建议检查数据源配置")

        invalid_sources = len(self.verified_sources) - valid_count
        if invalid_sources > 0:
            report["recommendations"].append(
                f"有{invalid_sources}个数据源无效，需要检查网络连接或API配置"
            )

        return report

    def save_validation_report(self, filepath: str = None):
        """
        保存验证报告

        Args:
            filepath: 文件路径，如果为None则使用默认路径
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data_validation_report_{timestamp}.json"

        report = self.generate_validation_report()

        try:
            with open(filepath, "w", encoding="utf - 8") as f:
                json.dump(report, f, indent = 2, ensure_ascii = False, default = str)

            logger.info(f"Validation report saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")
            return None


# 全局数据验证器实例
_data_validator = None


def get_data_validator() -> DataValidator:
    """获取数据验证器单例"""
    global _data_validator
    if _data_validator is None:
        _data_validator = DataValidator()
    return _data_validator


if __name__ == "__main__":
    # 测试数据验证器
    print("Testing Data Validator...")

    validator = DataValidator()

    # 验证股票数据
    print("\n1. Validating stock data...")
    stock_result = validator.validate_stock_data("0700.hk")
    print(
        f"Stock data validation: {stock_result['is_valid']}, quality: {stock_result.get('quality_score', 0):.2f}"
    )

    # 验证政府数据
    print("\n2. Validating government data...")
    gov_results = validator.validate_government_data()
    for source, result in gov_results.items():
        print(
            f"{source}: {result['is_valid']}, quality: {result.get('quality_score', 0):.2f}"
        )

    # 生成报告
    print("\n3. Generating validation report...")
    report = validator.generate_validation_report()
    print(f"Overall status: {report['overall_status']}")
    print(
        f"Valid sources: {report['summary']['valid_sources']}/{report['summary']['total_sources']}"
    )
    print(f"Average quality score: {report['summary']['average_quality_score']:.2f}")

    # 保存报告
    report_path = validator.save_validation_report()
    print(f"\nValidation report saved: {report_path}")

    print("\nData validator test completed!")
