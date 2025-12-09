#!/usr / bin / env python3
"""
數據質量驗證系統測試和演示
Data Quality Validation System Test and Demonstration

展示完整的數據質量驗證框架，包括：
1. 政府數據質量驗證
2. 股票數據質量驗證
3. 自動修復功能
4. 異常檢測
5. 報告生成
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# 導入驗證系統
from data_quality_validator import (
    DataQualityValidator,
    quick_data_quality_check,
    validate_government_data,
    validate_stock_data,
)
from enhanced_data_collector import (
    EnhancedGovernmentDataCollector,
    collect_all_government_data_with_validation,
    collect_government_data_with_validation,
)
from enhanced_stock_api import (
    EnhancedStockAPI,
    detect_market_anomalies,
    generate_data_quality_summary,
    get_stock_data_with_validation,
)

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataQualitySystemDemo:
    """數據質量驗證系統演示"""

    def __init__(self):
        self.validator = DataQualityValidator()
        self.output_dir = Path("data_quality_demo_results")
        self.output_dir.mkdir(exist_ok = True)

    def demo_government_data_validation(self):
        """演示政府數據驗證"""
        print("🏛️  政府數據質量驗證演示")
        print("=" * 50)

        # 創建測試數據
        test_data = self._create_test_government_data()

        # HIBOR數據驗證
        print("\n📊 HIBOR數據驗證:")
        hibor_report = validate_government_data(test_data["hibor"], "hibor")
        print(f"   質量評分: {hibor_report.quality_score:.1f}/100")
        print(f"   嚴重問題: {len(hibor_report.critical_issues)}")
        print(f"   高優先級問題: {len(hibor_report.high_issues)}")

        for issue in hibor_report.critical_issues:
            print(f"   ❌ {issue.message}")
            if issue.suggested_fix:
                print(f"      建議: {issue.suggested_fix}")

        # 匯率數據驗證
        print("\n💱 匯率數據驗證:")
        exchange_report = validate_government_data(
            test_data["exchange"], "exchange_rate"
        )
        print(f"   質量評分: {exchange_report.quality_score:.1f}/100")
        print(f"   嚴重問題: {len(exchange_report.critical_issues)}")
        print(f"   高優先級問題: {len(exchange_report.high_issues)}")

        # 保存報告
        self._save_report(hibor_report, "demo_hibor_quality_report.json")
        self._save_report(exchange_report, "demo_exchange_quality_report.json")

    def demo_stock_data_validation(self):
        """演示股票數據驗證"""
        print("\n📈 股票數據質量驗證演示")
        print("=" * 50)

        # 創建測試股票數據
        test_data = self._create_test_stock_data()

        # 高質量數據驗證
        print("\n✅ 高質量數據測試:")
        good_data_report = validate_stock_data(test_data["good_quality"])
        print(f"   質量評分: {good_data_report.quality_score:.1f}/100")
        print(
            f"   驗證狀態: {'通過' if len(good_data_report.critical_issues) == 0 else '失敗'}"
        )

        # 低質量數據驗證
        print("\n❌ 低質量數據測試:")
        poor_data_report = validate_stock_data(test_data["poor_quality"])
        print(f"   質量評分: {poor_data_report.quality_score:.1f}/100")
        print(f"   嚴重問題: {len(poor_data_report.critical_issues)}")
        print(f"   高優先級問題: {len(poor_data_report.high_issues)}")

        for issue in poor_data_report.critical_issues[:3]:  # 只顯示前3個問題
            print(f"   ❌ {issue.message}")

        # 異常數據驗證
        print("\n⚠️  異常數據測試:")
        anomaly_data_report = validate_stock_data(test_data["anomaly"])
        print(f"   質量評分: {anomaly_data_report.quality_score:.1f}/100")
        print(f"   檢測到的異常: {len(anomaly_data_report.high_issues)}")

        for issue in anomaly_data_report.high_issues:
            print(f"   ⚠️  {issue.message}")

        # 保存報告
        self._save_report(good_data_report, "demo_good_stock_quality.json")
        self._save_report(poor_data_report, "demo_poor_stock_quality.json")
        self._save_report(anomaly_data_report, "demo_anomaly_stock_quality.json")

    def demo_auto_fix_functionality(self):
        """演示自動修復功能"""
        print("\n🔧 自動修復功能演示")
        print("=" * 50)

        # 創建需要修復的數據
        broken_data = self._create_broken_data()

        # 政府數據修復
        print("\n🏛️  政府數據自動修復:")
        broken_gov_report = validate_government_data(broken_data["government"], "hibor")
        print(f"   修復前質量評分: {broken_gov_report.quality_score:.1f}/100")

        # 模擬修復過程
        fixed_gov_data = self._simulate_auto_fix_government_data(
            broken_data["government"]
        )
        fixed_gov_report = validate_government_data(fixed_gov_data, "hibor")
        print(f"   修復後質量評分: {fixed_gov_report.quality_score:.1f}/100")
        print(
            f"   質量提升: {fixed_gov_report.quality_score - broken_gov_report.quality_score:.1f} 分"
        )

        # 股票數據修復
        print("\n📈 股票數據自動修復:")
        broken_stock_report = validate_stock_data(broken_data["stock"])
        print(f"   修復前質量評分: {broken_stock_report.quality_score:.1f}/100")

        fixed_stock_data = self._simulate_auto_fix_stock_data(broken_data["stock"])
        fixed_stock_report = validate_stock_data(fixed_stock_data)
        print(f"   修復後質量評分: {fixed_stock_report.quality_score:.1f}/100")
        print(
            f"   質量提升: {fixed_stock_report.quality_score - broken_stock_report.quality_score:.1f} 分"
        )

    def demo_real_data_collection(self):
        """演示真實數據收集和驗證"""
        print("\n🌐 真實數據收集和驗證演示")
        print("=" * 50)

        async def collect_real_data():
            try:
                # 收集真實政府數據
                print("\n📊 收集真實政府數據...")
                gov_results = await collect_all_government_data_with_validation()

                successful_gov = [r for r in gov_results if r.success]
                print(f"   成功收集: {len(successful_gov)}/{len(gov_results)} 個數據源")

                for result in successful_gov:
                    if result.quality_report:
                        print(
                            f"   {result.source_name}: 質量評分 {result.quality_report.quality_score:.1f}"
                        )

                # 收集真實股票數據
                print("\n📈 收集真實股票數據...")
                stock_api = EnhancedStockAPI()
                symbols = ["0700.hk", "0941.hk"]  # 騰訊和移動

                stock_summary = stock_api.generate_data_quality_summary(symbols, 30)
                stats = stock_summary.get("overall_statistics", {})

                print(f"   收集成功率: {stats.get('collection_success_rate', 0):.1%}")
                print(f"   平均質量評分: {stats.get('average_quality_score', 0):.1f}")
                print(f"   驗證通過率: {stats.get('validation_pass_rate', 0):.1%}")

                return gov_results, stock_summary

            except Exception as e:
                print(f"   ❌ 真實數據收集失敗: {e}")
                return None, None

        # 運行異步收集
        return asyncio.run(collect_real_data())

    def demo_anomaly_detection(self):
        """演示異常檢測功能"""
        print("\n🔍 異常檢測功能演示")
        print("=" * 50)

        # 創建包含異常的數據
        anomaly_data = self._create_anomaly_data()

        # 價格異常檢測
        print("\n💰 價格異常檢測:")
        price_anomaly_report = validate_stock_data(anomaly_data["price_spike"])
        price_issues = [
            issue
            for issue in price_anomaly_report.high_issues
            if "跳變" in issue.message
        ]
        print(f"   檢測到價格異常: {len(price_issues)} 個")
        for issue in price_issues:
            print(f"   ⚠️  {issue.message}")

        # 成交量異常檢測
        print("\n📊 成交量異常檢測:")
        volume_anomaly_report = validate_stock_data(anomaly_data["volume_spike"])
        volume_issues = [
            issue
            for issue in volume_anomaly_report.medium_issues
            if "成交量" in issue.message
        ]
        print(f"   檢測到成交量異常: {len(volume_issues)} 個")
        for issue in volume_issues:
            print(f"   ⚠️  {issue.message}")

        # 停牌檢測
        print("\n🚫 停牌檢測:")
        halt_data = anomaly_data["trading_halt"]
        halt_report = validate_stock_data(halt_data)
        halt_issues = [
            issue for issue in halt_report.medium_issues if "交易日" in issue.message
        ]
        print(f"   檢測到潛在停牌: {len(halt_issues)} 個異常")

        # 實時異常檢測
        print("\n📡 實時異常檢測演示:")
        try:
            stock_api = EnhancedStockAPI()
            anomalies = stock_api.detect_market_anomalies("0700.hk", 10)  # 過去10天
            if "error" not in anomalies:
                print(
                    f"   0700.hk 異常檢測完成，發現 {len(anomalies['anomalies_detected'])} 種異常情況"
                )
                for anomaly in anomalies["anomalies_detected"]:
                    print(f"   - {anomaly['type']}: {anomaly.get('count', 0)} 次")
            else:
                print(f"   實時異常檢測失敗: {anomalies['error']}")
        except Exception as e:
            print(f"   實時異常檢測異常: {e}")

    def demo_quality_reporting(self):
        """演示質量報告生成"""
        print("\n📋 質量報告生成演示")
        print("=" * 50)

        # 生成綜合質量報告
        print("\n📊 生成綜合質量報告...")

        # 創建各種類型的測試數據
        test_datasets = {
            "government_hibor": self._create_test_government_data()["hibor"],
            "government_exchange": self._create_test_government_data()["exchange"],
            "stock_good": self._create_test_stock_data()["good_quality"],
            "stock_poor": self._create_test_stock_data()["poor_quality"],
        }

        # 驗證所有數據集
        reports = {}
        for name, data in test_datasets.items():
            if "government" in name:
                data_type = "hibor" if "hibor" in name else "exchange_rate"
                reports[name] = validate_government_data(data, data_type)
            else:
                reports[name] = validate_stock_data(data)

        # 生成摘要統計
        total_datasets = len(reports)
        passing_datasets = len(
            [r for r in reports.values() if len(r.critical_issues) == 0]
        )
        average_score = sum(r.quality_score for r in reports.values()) / total_datasets

        print(f"   總數據集: {total_datasets}")
        print(f"   驗證通過: {passing_datasets}")
        print(f"   平均質量評分: {average_score:.1f}")

        # 詳細報告
        print("\n📄 詳細質量報告:")
        for name, report in reports.items():
            print(f"\n   {name}:")
            print(f"     質量評分: {report.quality_score:.1f}/100")
            print(f"     嚴重問題: {len(report.critical_issues)}")
            print(f"     高優先級問題: {len(report.high_issues)}")

            # 主要問題摘要
            all_issues = report.critical_issues + report.high_issues
            if all_issues:
                print(f"     主要問題:")
                for issue in all_issues[:3]:  # 只顯示前3個
                    print(f"       - {issue.message}")

        # 保存報告
        print(f"\n💾 報告已保存到: {self.output_dir}")
        for name, report in reports.items():
            filename = f"comprehensive_report_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.output_dir / filename
            self._save_report(report, filename)

    def _create_test_government_data(self) -> dict:
        """創建測試政府數據"""
        base_date = datetime.now() - timedelta(days = 30)

        # 正常HIBOR數據
        hibor_data = []
        for i in range(30):
            date = base_date + timedelta(days = i)
            hibor_data.append(
                {
                    "end_of_day": date.strftime("%Y-%m-%d"),
                    "ir_overnight": 3.5 + np.random.normal(0, 0.2),
                    "ir_1_week": 3.7 + np.random.normal(0, 0.2),
                    "ir_1_month": 4.0 + np.random.normal(0, 0.2),
                }
            )

        # 添加一些異常數據
        hibor_data[5]["ir_overnight"] = -1.0  # 負利率（異常）
        hibor_data[10]["ir_1_week"] = 150.0  # 過高利率（異常）

        # 正常匯率數據
        exchange_data = []
        for i in range(30):
            date = base_date + timedelta(days = i)
            exchange_data.append(
                {
                    "end_of_day": date.strftime("%Y-%m-%d"),
                    "usd": 7.8 + np.random.normal(0, 0.05),
                    "cny": 1.2 + np.random.normal(0, 0.02),
                }
            )

        # 添加異常匯率數據
        exchange_data[8]["usd"] = 0.8  # 錯誤匯率
        exchange_data[15]["cny"] = 15.0  # 錯誤匯率

        return {"hibor": hibor_data, "exchange": exchange_data}

    def _create_test_stock_data(self) -> dict:
        """創建測試股票數據"""
        dates = pd.date_range(start="2024 - 01 - 01", periods = 60, freq="D")
        dates = dates[dates.weekday < 5]  # 只保留工作日

        # 高質量數據
        good_quality_data = pd.DataFrame(
            {
                "open": 100 + np.random.normal(0, 2, len(dates)),
                "high": 105 + np.random.normal(0, 2, len(dates)),
                "low": 95 + np.random.normal(0, 2, len(dates)),
                "close": 100 + np.random.normal(0, 1, len(dates)),
                "volume": np.random.randint(1000000, 5000000, len(dates)),
            },
            index = dates,
        )

        # 確保OHLC邏輯正確
        good_quality_data["high"] = (
            good_quality_data[["open", "close"]].max(axis = 1) * 1.02
        )
        good_quality_data["low"] = (
            good_quality_data[["open", "close"]].min(axis = 1) * 0.98
        )

        # 低質量數據（包含問題）
        poor_quality_data = good_quality_data.copy()
        poor_quality_data.iloc[10:15, 1] = (
            poor_quality_data.iloc[10:15, 3] * 0.8
        )  # high < close
        poor_quality_data.iloc[20:25, 2] = (
            poor_quality_data.iloc[20:25, 0] * 1.2
        )  # low > open
        poor_quality_data.iloc[30, 0] = -50  # 負價格
        poor_quality_data.iloc[35:40, 3] = 0  # 零價格

        return {"good_quality": good_quality_data, "poor_quality": poor_quality_data}

    def _create_anomaly_data(self) -> dict:
        """創建異常檢測測試數據"""
        dates = pd.date_range(start="2024 - 01 - 01", periods = 30, freq="D")
        dates = dates[dates.weekday < 5]

        # 價格異常數據
        price_spike_data = pd.DataFrame(
            {
                "open": 100 + np.random.normal(0, 1, len(dates)),
                "high": 102 + np.random.normal(0, 1, len(dates)),
                "low": 98 + np.random.normal(0, 1, len(dates)),
                "close": 100 + np.random.normal(0, 0.5, len(dates)),
                "volume": np.random.randint(1000000, 3000000, len(dates)),
            },
            index = dates,
        )

        # 添加價格異常跳變
        price_spike_data.iloc[10, 3] = 150  # 50%跳變
        price_spike_data.iloc[20, 3] = 60  # 40%下跌

        # 成交量異常數據
        volume_spike_data = price_spike_data.copy()
        volume_spike_data.iloc[15, 4] = 20000000  # 成交量異常放

        # 停牌數據（價格不變）
        trading_halt_data = price_spike_data.copy()
        trading_halt_data.iloc[8:12, 3] = 100  # 連續幾天價格不變

        return {
            "price_spike": price_spike_data,
            "volume_spike": volume_spike_data,
            "trading_halt": trading_halt_data,
        }

    def _create_broken_data(self) -> dict:
        """創建需要修復的破損數據"""
        # 政府數據問題
        broken_gov = [
            {"end_of_day": "2024 - 01 - 01", "ir_overnight": 350},  # 需要除以100
            {"end_of_day": "2024 - 01 - 02", "ir_overnight": -2},  # 負利率
            {"end_of_day": "2024 - 01 - 03"},  # 缺少利率字段
        ]

        # 股票數據問題
        dates = pd.date_range(start="2024 - 01 - 01", periods = 10, freq="D")
        broken_stock = pd.DataFrame(
            {
                "close": [100, 150, 80, 200, 50, -10, 0, 120, 130, 110],  # 包含異常值
            },
            index = dates,
        )

        return {"government": broken_gov, "stock": broken_stock}

    def _simulate_auto_fix_government_data(self, data: list) -> list:
        """模擬政府數據自動修復"""
        fixed_data = []
        for record in data:
            fixed_record = record.copy()

            # 修復利率單位問題
            if "ir_overnight" in fixed_record:
                if fixed_record["ir_overnight"] > 100:
                    fixed_record["ir_overnight"] = fixed_record["ir_overnight"] / 100
                if fixed_record["ir_overnight"] < 0:
                    fixed_record["ir_overnight"] = 0

            # 添加缺失字段
            if "ir_overnight" not in fixed_record:
                fixed_record["ir_overnight"] = 3.5

            fixed_data.append(fixed_record)

        return fixed_data

    def _simulate_auto_fix_stock_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """模擬股票數據自動修復"""
        fixed_data = data.copy()

        # 修復價格邏輯
        if "close" in fixed_data.columns:
            # 填充缺失的OHLC字段
            if "open" not in fixed_data.columns:
                fixed_data["open"] = (
                    fixed_data["close"].shift(1).fillna(fixed_data["close"])
                )
            if "high" not in fixed_data.columns:
                fixed_data["high"] = fixed_data["close"] * 1.01
            if "low" not in fixed_data.columns:
                fixed_data["low"] = fixed_data["close"] * 0.99
            if "volume" not in fixed_data.columns:
                fixed_data["volume"] = 1000000

            # 修復異常值
            fixed_data["close"] = fixed_data["close"].clip(lower = 0.01, upper = 10000)
            fixed_data["high"] = np.maximum(
                fixed_data["high"], fixed_data[["open", "close"]].max(axis = 1)
            )
            fixed_data["low"] = np.minimum(
                fixed_data["low"], fixed_data[["open", "close"]].min(axis = 1)
            )

        return fixed_data

    def _save_report(self, report, filename: str):
        """保存質量報告"""
        filepath = self.output_dir / filename

        # 轉換報告為可序列化格式
        report_dict = {
            "data_source": report.data_source,
            "validation_timestamp": report.validation_timestamp.isoformat(),
            "total_records": report.total_records,
            "valid_records": report.valid_records,
            "quality_score": report.quality_score,
            "summary": report.summary,
            "critical_issues": [
                {
                    "rule_name": issue.rule_name,
                    "message": issue.message,
                    "severity": issue.severity,
                    "suggested_fix": issue.suggested_fix,
                }
                for issue in report.critical_issues
            ],
            "high_issues": [
                {
                    "rule_name": issue.rule_name,
                    "message": issue.message,
                    "severity": issue.severity,
                    "suggested_fix": issue.suggested_fix,
                }
                for issue in report.high_issues
            ],
        }

        with open(filepath, "w", encoding="utf - 8") as f:
            json.dump(report_dict, f, ensure_ascii = False, indent = 2)

    def run_complete_demo(self):
        """運行完整演示"""
        print("🚀 數據質量驗證系統完整演示")
        print("=" * 60)

        start_time = time.time()

        try:
            # 1. 政府數據驗證
            self.demo_government_data_validation()

            # 2. 股票數據驗證
            self.demo_stock_data_validation()

            # 3. 自動修復功能
            self.demo_auto_fix_functionality()

            # 4. 異常檢測
            self.demo_anomaly_detection()

            # 5. 質量報告
            self.demo_quality_reporting()

            # 6. 真實數據收集（可選，可能需要網絡）
            try:
                self.demo_real_data_collection()
            except Exception as e:
                print(f"\n⚠️  真實數據收集跳過（網絡問題）: {e}")

        except Exception as e:
            print(f"\n❌ 演示過程中發生錯誤: {e}")
            import traceback

            traceback.print_exc()

        finally:
            end_time = time.time()
            print(f"\n✅ 演示完成，耗時: {end_time - start_time:.2f} 秒")
            print(f"📁 所有報告已保存到: {self.output_dir}")


if __name__ == "__main__":
    # 運行演示
    demo = DataQualitySystemDemo()
    demo.run_complete_demo()
