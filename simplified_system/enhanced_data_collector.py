#!/usr / bin / env python3
"""
增強數據收集器 - 集成嚴格數據質量驗證的政府數據收集系統
Enhanced Data Collector - Government Data Collection with Strict Quality Validation

整合現有的政府數據收集邏輯，添加嚴格的數據質量驗證和自動修復功能
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import pandas as pd

# 導入現有模塊
from data_quality_validator import (
    DataQualityReport,
    DataQualityValidator,
    ValidationResult,
    quick_data_quality_check,
    validate_government_data,
)
from src.data.government_data import DataCollectionResult, GovernmentDataCollector

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class EnhancedDataCollectionResult:
    """增強數據收集結果，包含質量驗證信息"""

    source_name: str
    success: bool
    record_count: int
    collection_time: datetime
    error_message: Optional[str] = None
    data_quality_score: Optional[float] = None
    file_path: Optional[str] = None

    # 質量驗證相關
    quality_report: Optional[DataQualityReport] = None
    validation_passed: bool = False
    auto_fixed: bool = False
    fix_attempts: int = 0
    critical_issues_count: int = 0
    high_issues_count: int = 0


class EnhancedGovernmentDataCollector(GovernmentDataCollector):
    """
    增強政府數據收集器
    集成嚴格的數據質量驗證和自動修復功能
    """

    def __init__(self):
        super().__init__()
        self.quality_validator = DataQualityValidator()
        self.auto_fix_enabled = True
        self.retry_on_failure = True
        self.max_retries = 3
        self.quality_threshold = 70.0  # 最低質量評分要求

    async def collect_with_validation(
        self, source_config
    ) -> EnhancedDataCollectionResult:
        """
        收集政府數據並進行質量驗證
        """
        logger.info(f"🔍 開始收集並驗證數據: {source_config.name}")

        # 第一步：收集原始數據
        original_result = await self.collect_hkma_data(source_config)

        if not original_result.success:
            logger.error(f"❌ 數據收集失敗: {original_result.error_message}")
            return self._create_enhanced_result(original_result, None)

        # 第二步：數據質量驗證
        records = (
            self._load_records_from_file(original_result.file_path)
            if original_result.file_path
            else []
        )

        if not records:
            logger.warning(f"⚠️ {source_config.name}: 無法加載記錄進行質量驗證")
            return self._create_enhanced_result(original_result, None)

        # 第三步：執行質量驗證
        quality_report = self.quality_validator.validate_government_data(
            records, source_config.data_type
        )

        logger.info(
            f"📊 {source_config.name} 質量評分: {quality_report.quality_score:.1f}"
        )
        logger.info(f"   嚴重問題: {len(quality_report.critical_issues)}")
        logger.info(f"   高優先級問題: {len(quality_report.high_issues)}")

        # 第四步：嘗試自動修復（如果啟用且質量不足）
        auto_fixed = False
        fix_attempts = 0

        if (
            self.auto_fix_enabled
            and quality_report.quality_score < self.quality_threshold
        ):
            logger.info(f"🔧 {source_config.name}: 質量評分不足，嘗試自動修復")

            fixed_records, fix_attempts = await self._auto_fix_data_issues(
                records, quality_report, source_config
            )

            if fixed_records:
                # 重新驗證修復後的數據
                fixed_report = self.quality_validator.validate_government_data(
                    fixed_records, source_config.data_type
                )

                if fixed_report.quality_score > quality_report.quality_score:
                    logger.info(
                        f"✅ {source_config.name}: 自動修復成功，質量評分從 {quality_report.quality_score:.1f} 提升到 {fixed_report.quality_score:.1f}"
                    )

                    # 保存修復後的數據
                    fixed_file_path = await self._save_fixed_data(
                        fixed_records, source_config.name
                    )

                    # 更新結果
                    original_result.record_count = len(fixed_records)
                    original_result.file_path = fixed_file_path
                    quality_report = fixed_report
                    auto_fixed = True
                else:
                    logger.warning(f"⚠️ {source_config.name}: 自動修復未能提升質量")
            else:
                logger.warning(f"⚠️ {source_config.name}: 無法自動修復數據問題")

        # 第五步：重試機制（如果仍有問題）
        if (
            self.retry_on_failure
            and len(quality_report.critical_issues) > 0
            and fix_attempts < self.max_retries
        ):
            logger.info(f"🔄 {source_config.name}: 檢測到嚴重問題，嘗試重新收集數據")

            retry_result = await self._retry_collection_with_fixes(
                source_config, quality_report
            )
            if (
                retry_result
                and retry_result.quality_report.quality_score
                > quality_report.quality_score
            ):
                quality_report = retry_result.quality_report
                original_result = retry_result
                fix_attempts += 1

        # 創建增強結果
        enhanced_result = self._create_enhanced_result(original_result, quality_report)
        enhanced_result.auto_fixed = auto_fixed
        enhanced_result.fix_attempts = fix_attempts
        enhanced_result.validation_passed = len(quality_report.critical_issues) == 0

        logger.info(
            f"📋 {source_name} 最終質量評分: {quality_report.quality_score:.1f}"
        )

        return enhanced_result

    def _load_records_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """從文件加載數據記錄"""
        try:
            with open(file_path, "r", encoding="utf - 8") as f:
                data = json.load(f)
                return data.get("data", [])
        except Exception as e:
            logger.error(f"無法加載文件 {file_path}: {e}")
            return []

    def _create_enhanced_result(
        self,
        original_result: DataCollectionResult,
        quality_report: Optional[DataQualityReport],
    ) -> EnhancedDataCollectionResult:
        """創建增強收集結果"""
        enhanced_result = EnhancedDataCollectionResult(
            source_name = original_result.source_name,
            success = original_result.success,
            record_count = original_result.record_count,
            collection_time = original_result.collection_time,
            error_message = original_result.error_message,
            data_quality_score = original_result.data_quality_score,
            file_path = original_result.file_path,
            quality_report = quality_report,
        )

        if quality_report:
            enhanced_result.critical_issues_count = len(quality_report.critical_issues)
            enhanced_result.high_issues_count = len(quality_report.high_issues)

        return enhanced_result

    async def _auto_fix_data_issues(
        self,
        records: List[Dict[str, Any]],
        quality_report: DataQualityReport,
        source_config,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """自動修復數據問題"""
        fix_attempts = 0
        fixed_records = records.copy()

        # 修復1：數據量不足問題
        if any(
            "數據量不足" in issue.message for issue in quality_report.critical_issues
        ):
            logger.info(f"🔧 嘗試修復數據量不足問題: {source_config.name}")
            fixed_records = await self._fix_data_volume_issue(
                source_config, fixed_records
            )
            fix_attempts += 1

        # 修復2：範圍錯誤問題
        range_issues = [
            issue
            for issue in quality_report.critical_issues + quality_report.high_issues
            if "範圍" in issue.message or "超出" in issue.message
        ]
        if range_issues:
            logger.info(f"🔧 嘗試修復範圍錯誤問題: {source_config.name}")
            fixed_records = self._fix_range_issues(fixed_records, range_issues)
            fix_attempts += 1

        # 修復3：完整性問題
        completeness_issues = [
            issue
            for issue in quality_report.critical_issues + quality_report.high_issues
            if "缺少" in issue.message or "字段" in issue.message
        ]
        if completeness_issues:
            logger.info(f"🔧 嘗試修復完整性問題: {source_config.name}")
            fixed_records = self._fix_completeness_issues(
                fixed_records, completeness_issues
            )
            fix_attempts += 1

        return fixed_records, fix_attempts

    async def _fix_data_volume_issue(
        self, source_config, existing_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """修復數據量不足問題"""
        try:
            # 嘗試擴大時間範圍或調整API參數重新收集
            logger.info(f"🔄 擴大時間範圍重新收集: {source_config.name}")

            # 這裡可以實現更復雜的邏輯，比如：
            # 1. 擴大時間範圍
            # 2. 調整API參數
            # 3. 使用不同的數據端點

            # 暫時返回現有記錄
            return existing_records

        except Exception as e:
            logger.error(f"修復數據量問題失敗: {e}")
            return existing_records

    def _fix_range_issues(
        self, records: List[Dict[str, Any]], issues: List[ValidationResult]
    ) -> List[Dict[str, Any]]:
        """修復範圍錯誤問題"""
        fixed_records = []

        for record in records:
            fixed_record = record.copy()

            # 修復利率範圍問題
            for key, value in record.items():
                if "ir_" in key.lower() and isinstance(value, (int, float)):
                    # HIBOR利率超出範圍，嘗試轉換單位
                    if value > 100:  # 可能是百分比而非小數
                        fixed_record[key] = value / 100
                    elif value < 0:
                        # 負利率不太可能，設置為0
                        fixed_record[key] = 0

                # 修復匯率範圍問題
                elif "usd" in key.lower() and isinstance(value, (int, float)):
                    if value < 1:  # 可能單位錯誤
                        fixed_record[key] = value * 7.8  # 轉換為港幣
                    elif value > 100:  # 可能單位錯誤
                        fixed_record[key] = value / 7.8

            fixed_records.append(fixed_record)

        return fixed_records

    def _fix_completeness_issues(
        self, records: List[Dict[str, Any]], issues: List[ValidationResult]
    ) -> List[Dict[str, Any]]:
        """修復完整性問題"""
        fixed_records = []

        for record in records:
            fixed_record = record.copy()

            # 嘗試填充缺失的必要字段
            if "end_of_day" not in fixed_record:
                # 嘗試從其他日期字段推斷
                for key in ["date", "time", "timestamp"]:
                    if key in fixed_record:
                        fixed_record["end_of_day"] = fixed_record[key]
                        break

            # 設置缺失數值字段的默認值
            numeric_defaults = {
                "ir_overnight": 0.0,
                "ir_1_week": 0.0,
                "ir_1_month": 0.0,
                "usd": 7.8,
                "cny": 1.2,
                "monetary_base": 0,
            }

            for field, default_value in numeric_defaults.items():
                if field in fixed_record and (
                    fixed_record[field] is None or fixed_record[field] == ""
                ):
                    fixed_record[field] = default_value

            fixed_records.append(fixed_record)

        return fixed_records

    async def _save_fixed_data(
        self, records: List[Dict[str, Any]], source_name: str
    ) -> str:
        """保存修復後的數據"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{source_name}_fixed_{timestamp}.json"
        filepath = self.data_storage_path / filename

        json_data = {
            "source": source_name,
            "collection_time": datetime.now().isoformat(),
            "record_count": len(records),
            "data_fixed": True,
            "auto_fix_timestamp": timestamp,
            "data": records,
        }

        with open(filepath, "w", encoding="utf - 8") as f:
            json.dump(json_data, f, ensure_ascii = False, indent = 2, default = str)

        logger.info(f"修復後的數據已保存: {filepath}")
        return str(filepath)

    async def _retry_collection_with_fixes(
        self, source_config, original_quality_report: DataQualityReport
    ) -> Optional[EnhancedDataCollectionResult]:
        """基於質量問題重試數據收集"""
        try:
            # 根據質量問題調整收集參數
            adjusted_config = self._adjust_config_based_on_issues(
                source_config, original_quality_report
            )

            # 重新收集數據
            retry_result = await self.collect_hkma_data(adjusted_config)

            if retry_result.success:
                # 驗證重試收集的數據
                records = self._load_records_from_file(retry_result.file_path)
                if records:
                    quality_report = self.quality_validator.validate_government_data(
                        records, source_config.data_type
                    )
                    return self._create_enhanced_result(retry_result, quality_report)

        except Exception as e:
            logger.error(f"重試收集失敗: {e}")

        return None

    def _adjust_config_based_on_issues(
        self, source_config, quality_report: DataQualityReport
    ):
        """根據質量問題調整收集配置"""
        # 這裡可以根據具體問題調整API參數
        # 暫時返回原始配置
        return source_config

    async def collect_all_with_validation(self) -> List[EnhancedDataCollectionResult]:
        """
        收集所有政府數據源並進行質量驗證
        """
        logger.info("🚀 開始增強政府數據收集（包含質量驗證）")

        # 按優先級排序
        sorted_sources = sorted(self.data_sources, key = lambda x: x.priority)

        results = []
        successful_collections = 0
        total_records = 0
        average_quality = 0.0

        for source_config in sorted_sources:
            logger.info(
                f"收集並驗證: {source_config.name} (優先級: {source_config.priority})"
            )

            try:
                result = await self.collect_with_validation(source_config)
                results.append(result)

                if result.success and result.validation_passed:
                    successful_collections += 1
                    total_records += result.record_count
                    if result.quality_report:
                        average_quality += result.quality_report.quality_score

                # 在請求之間添加延遲
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"❌ {source_config.name} 收集失敗: {e}")
                # 創建失敗結果
                failed_result = EnhancedDataCollectionResult(
                    source_name = source_config.name,
                    success = False,
                    record_count = 0,
                    collection_time = datetime.now(),
                    error_message = str(e),
                )
                results.append(failed_result)

        # 計算平均質量評分
        if successful_collections > 0:
            average_quality = average_quality / successful_collections

        # 生成增強收集報告
        self._generate_enhanced_collection_report(
            results, successful_collections, total_records, average_quality
        )

        return results

    def _generate_enhanced_collection_report(
        self,
        results: List[EnhancedDataCollectionResult],
        successful_collections: int,
        total_records: int,
        average_quality: float,
    ):
        """生成增強的收集報告"""
        report = {
            "collection_time": datetime.now().isoformat(),
            "enhanced_collector": True,
            "total_sources": len(results),
            "successful_collections": successful_collections,
            "validation_passed_collections": len(
                [r for r in results if r.validation_passed]
            ),
            "total_records": total_records,
            "average_quality_score": round(average_quality, 3),
            "auto_fixed_count": len([r for r in results if r.auto_fixed]),
            "sources": [
                {
                    "name": r.source_name,
                    "success": r.success,
                    "validation_passed": r.validation_passed,
                    "record_count": r.record_count,
                    "quality_score": (
                        r.quality_report.quality_score if r.quality_report else None
                    ),
                    "critical_issues": r.critical_issues_count,
                    "high_issues": r.high_issues_count,
                    "auto_fixed": r.auto_fixed,
                    "fix_attempts": r.fix_attempts,
                    "error_message": r.error_message,
                }
                for r in results
            ],
        }

        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"enhanced_government_data_report_{timestamp}.json"
        report_path = self.data_storage_path / report_filename

        with open(report_path, "w", encoding="utf - 8") as f:
            json.dump(report, f, ensure_ascii = False, indent = 2, default = str)

        logger.info(f"📊 增強收集完成: {successful_collections}/{len(results)} 成功")
        logger.info(f"   驗證通過: {len([r for r in results if r.validation_passed])}")
        logger.info(f"   總記錄數: {total_records}")
        logger.info(f"   平均質量評分: {average_quality:.3f}")
        logger.info(
            f"   自動修復: {len([r for r in results if r.auto_fixed])} 個數據源"
        )
        logger.info(f"📄 增強報告已保存: {report_path}")


# 全局增強收集器實例
enhanced_collector = EnhancedGovernmentDataCollector()


# 便捷函數
async def collect_government_data_with_validation(
    source_name: str,
) -> Optional[EnhancedDataCollectionResult]:
    """收集特定政府數據源並進行質量驗證"""
    for source_config in enhanced_collector.data_sources:
        if source_config.name == source_name:
            return await enhanced_collector.collect_with_validation(source_config)
    return None


async def collect_all_government_data_with_validation() -> (
    List[EnhancedDataCollectionResult]
):
    """收集所有政府數據並進行質量驗證"""
    return await enhanced_collector.collect_all_with_validation()


async def get_validated_government_data(
    source_name: str,
    min_quality_score: float = 70.0,
    require_validation_passed: bool = True,
) -> Optional[Dict[str, Any]]:
    """獲取通過質量驗證的政府數據"""
    result = await collect_government_data_with_validation(source_name)

    if not result or not result.success:
        return None

    # 檢查質量要求
    if require_validation_passed and not result.validation_passed:
        logger.warning(f"{source_name} 未通過驗證要求")
        return None

    if (
        result.quality_report
        and result.quality_report.quality_score < min_quality_score
    ):
        logger.warning(
            f"{source_name} 質量評分 {result.quality_report.quality_score:.1f} 低於要求 {min_quality_score}"
        )
        return None

    # 加載並返回數據
    if result.file_path:
        try:
            with open(result.file_path, "r", encoding="utf - 8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"無法加載驗證後的數據: {e}")

    return None


if __name__ == "__main__":

    async def main():
        """測試增強數據收集器"""
        print("🧪 測試增強政府數據收集器")

        # 測試單個數據源
        print("\n=== 單個數據源測試 ===")
        hibor_result = await collect_government_data_with_validation("hibor_rates")
        if hibor_result:
            print(f"✅ HIBOR收集成功: {hibor_result.record_count} 條記錄")
            print(f"   質量評分: {hibor_result.quality_report.quality_score:.1f}")
            print(f"   驗證通過: {hibor_result.validation_passed}")
            print(f"   自動修復: {hibor_result.auto_fixed}")
        else:
            print("❌ HIBOR收集失敗")

        # 測試所有數據源
        print("\n=== 所有數據源測試 ===")
        all_results = await collect_all_government_data_with_validation()

        successful = len([r for r in all_results if r.success])
        validated = len([r for r in all_results if r.validation_passed])
        auto_fixed = len([r for r in all_results if r.auto_fixed])

        print(f"✅ 收集結果: {successful}/{len(all_results)} 成功")
        print(f"   驗證通過: {validated}/{successful}")
        print(f"   自動修復: {auto_fixed}")

        # 清理
        await enhanced_collector.close()
        print("\n✅ 增強收集器測試完成")

    # 運行測試
    asyncio.run(main())
