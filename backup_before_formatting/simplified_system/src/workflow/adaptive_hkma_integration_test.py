"""
適應性系統與HKMA真實數據集成測試
Adaptive System Integration with Real HKMA Data
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# 添加模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.workflow.adaptive_market_system import AdaptiveMarketSystem
from src.data.government_data import GovernmentDataCollector

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdaptiveHKMAIntegrationTest:
    """適應性HKMA集成測試類"""

    def __init__(self):
        self.adaptive_system = AdaptiveMarketSystem()
        self.data_collector = GovernmentDataCollector()

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """運行完整的適應性HKMA測試"""
        logger.info("🚀 開始適應性HKMA系統集成測試")
        print("=" * 60)
        print("🎯 適應性市場系統 + HKMA真實數據集成測試")
        print("=" * 60)

        try:
            # 步驟1: 收集真實HKMA數據
            print("\n📊 步驟1: 收集HKMA真實數據...")
            raw_data = self._collect_hkma_data()

            if not raw_data:
                logger.error("❌ 無法收集HKMA數據，測試終止")
                return self._create_error_result("數據收集失敗")

            print(f"✅ 成功收集 {len(raw_data)} 個數據源")

            # 步驟2: 數據預處理
            print("\n🔄 步驟2: 數據預處理...")
            processed_data = self._preprocess_data(raw_data)

            # 步驟3: 運行適應性分析
            print("\n🧠 步驟3: 運行適應性市場分析...")
            adaptive_results = self.adaptive_system.run_adaptive_analysis(processed_data)

            # 步驟4: 與傳統方法比較
            print("\n📈 步驟4: 與傳統固定參數方法比較...")
            comparison_results = self._compare_with_traditional_method(processed_data)

            # 步驟5: 生成完整報告
            print("\n📋 步驟5: 生成分析報告...")
            final_report = self._generate_comprehensive_report(
                adaptive_results, comparison_results, raw_data
            )

            # 保存結果
            self._save_test_results(final_report)

            # 顯示結果摘要
            self._display_results_summary(final_report)

            logger.info("🎉 適應性HKMA集成測試完成")
            return final_report

        except Exception as e:
            logger.error(f"❌ 測試過程中發生錯誤: {e}")
            return self._create_error_result(str(e))

    def _collect_hkma_data(self) -> Dict[str, Any]:
        """收集HKMA真實數據"""
        try:
            # 使用已有的政府數據收集器
            raw_data = self.data_collector.collect_all_sources()
            return raw_data

        except Exception as e:
            logger.error(f"❌ 收集HKMA數據失敗: {e}")
            return {}

    def _preprocess_data(self, raw_data: Dict[str, Any]) -> Dict[str, pd.Series]:
        """預處理數據為pandas Series"""
        processed_data = {}

        for source_name, data in raw_data.items():
            try:
                if isinstance(data, dict) and 'data' in data:
                    # 處理API響應格式
                    data_list = data['data']
                    if not data_list:
                        continue

                    # 提取數值和日期
                    dates = []
                    values = []

                    for item in data_list:
                        # 嘗試多種日期字段
                        date_field = None
                        for field in ['end_of_day', 'date', 'period', 'time']:
                            if field in item:
                                date_field = field
                                break

                        if not date_field:
                            continue

                        # 嘗試多種數值字段
                        value_field = None
                        for field in ['rate', 'value', 'amount', 'price', 'close']:
                            if field in item and item[field] is not None:
                                value_field = field
                                break

                        if not value_field:
                            continue

                        try:
                            # 解析日期
                            date_str = item[date_field]
                            if isinstance(date_str, str):
                                date = pd.to_datetime(date_str)
                            else:
                                continue

                            # 解析數值
                            value = float(item[value_field])

                            dates.append(date)
                            values.append(value)

                        except (ValueError, TypeError) as e:
                            continue

                    if dates and values:
                        # 創建Series並按日期排序
                        series = pd.Series(values, index=dates)
                        series = series.sort_index()
                        processed_data[source_name] = series
                        logger.info(f"✅ {source_name}: {len(series)} 條記錄")

                elif isinstance(data, list):
                    # 處理列表格式數據
                    dates = []
                    values = []

                    for item in data:
                        if isinstance(item, dict):
                            date_field = None
                            for field in ['date', 'period', 'end_of_day']:
                                if field in item:
                                    date_field = field
                                    break

                            value_field = None
                            for field in ['rate', 'value', 'amount']:
                                if field in item and item[field] is not None:
                                    value_field = field
                                    break

                            if date_field and value_field:
                                try:
                                    date = pd.to_datetime(item[date_field])
                                    value = float(item[value_field])
                                    dates.append(date)
                                    values.append(value)
                                except (ValueError, TypeError):
                                    continue

                    if dates and values:
                        series = pd.Series(values, index=dates)
                        series = series.sort_index()
                        processed_data[source_name] = series
                        logger.info(f"✅ {source_name}: {len(series)} 條記錄")

            except Exception as e:
                logger.warning(f"⚠️ 處理 {source_name} 數據失敗: {e}")
                continue

        return processed_data

    def _compare_with_traditional_method(self, processed_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """與傳統固定參數方法比較"""
        logger.info("🔄 與傳統固定參數方法比較...")

        traditional_results = {}
        adaptive_results = {}

        for source_name, data in processed_data.items():
            try:
                # 傳統固定參數分析
                traditional_score = self._traditional_analysis(data)
                traditional_results[source_name] = traditional_score

                # 適應性分析結果
                adaptive_analysis = self.adaptive_system.analyzer.analyze_with_adaptation(data, source_name)
                adaptive_score = adaptive_analysis["adaptive_indicators"].get("total_score", 0)
                adaptive_results[source_name] = adaptive_score

                logger.info(f"📊 {source_name}: 傳統={traditional_score:.3f}, 適應性={adaptive_score:.3f}")

            except Exception as e:
                logger.warning(f"⚠️ {source_name} 比較分析失敗: {e}")
                continue

        # 計算改進幅度
        improvements = {}
        for source in traditional_results:
            if source in adaptive_results:
                traditional = traditional_results[source]
                adaptive = adaptive_results[source]
                if traditional > 0:
                    improvement = (adaptive - traditional) / traditional * 100
                    improvements[source] = improvement

        return {
            "traditional_scores": traditional_results,
            "adaptive_scores": adaptive_results,
            "improvements": improvements,
            "average_improvement": np.mean(list(improvements.values())) if improvements else 0,
            "comparison_count": len(improvements)
        }

    def _traditional_analysis(self, data: pd.Series) -> float:
        """傳統固定參數技術分析"""
        try:
            if len(data) < 14:
                return 0.0

            # 固定參數RSI
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            current_rsi = rsi.iloc[-1] if not rsi.empty else 50.0

            # 固定參數MACD
            exp1 = data.ewm(span=12).mean()
            exp2 = data.ewm(span=26).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=9).mean()

            # 簡單評分
            score = 0.0

            # RSI評分
            if 30 <= current_rsi <= 70:
                score += 0.4
            elif current_rsi < 30 or current_rsi > 70:
                score += 0.6

            # MACD評分
            if len(macd_line) > 0 and len(signal_line) > 0:
                if macd_line.iloc[-1] > signal_line.iloc[-1]:
                    score += 0.3
                else:
                    score += 0.1

            # 趨勢評分 (簡單移動平均)
            short_ma = data.rolling(window=10).mean()
            long_ma = data.rolling(window=30).mean()

            if len(short_ma) > 0 and len(long_ma) > 0:
                if short_ma.iloc[-1] > long_ma.iloc[-1]:
                    score += 0.3
                else:
                    score += 0.1

            return min(score, 1.0)

        except Exception as e:
            logger.warning(f"傳統分析失敗: {e}")
            return 0.0

    def _generate_comprehensive_report(self, adaptive_results: Dict[str, Any],
                                     comparison_results: Dict[str, Any],
                                     raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成綜合分析報告"""
        logger.info("📝 生成綜合分析報告...")

        report = {
            "test_info": {
                "test_type": "adaptive_hkma_integration",
                "timestamp": datetime.now().isoformat(),
                "data_sources_count": len(raw_data),
                "successful_analysis": len(adaptive_results.get("source_analyses", {}))
            },
            "adaptive_analysis": adaptive_results,
            "performance_comparison": comparison_results,
            "data_quality_assessment": self._assess_data_quality(raw_data),
            "market_regime_analysis": self._analyze_market_regimes(adaptive_results),
            "recommendations": self._generate_recommendations(adaptive_results, comparison_results)
        }

        return report

    def _assess_data_quality(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """評估數據質量"""
        quality_metrics = {}

        for source_name, data in raw_data.items():
            try:
                if isinstance(data, dict) and 'data' in data:
                    data_list = data['data']
                    record_count = len(data_list)
                    latest_record = data_list[0] if data_list else None

                    # 檢查數據完整性
                    completeness = self._check_data_completeness(data_list)

                    # 檢查數據新鮮度
                    freshness = self._check_data_freshness(latest_record)

                    quality_metrics[source_name] = {
                        "record_count": record_count,
                        "completeness_score": completeness,
                        "freshness_score": freshness,
                        "overall_quality": (completeness + freshness) / 2
                    }

            except Exception as e:
                quality_metrics[source_name] = {
                    "record_count": 0,
                    "completeness_score": 0,
                    "freshness_score": 0,
                    "overall_quality": 0,
                    "error": str(e)
                }

        return quality_metrics

    def _check_data_completeness(self, data_list: List[Dict]) -> float:
        """檢查數據完整性"""
        if not data_list:
            return 0.0

        complete_records = 0
        required_fields = ['date', 'rate']  # 基本要求字段

        for record in data_list:
            if all(field in record for field in required_fields):
                complete_records += 1

        return complete_records / len(data_list)

    def _check_data_freshness(self, latest_record: Dict) -> float:
        """檢查數據新鮮度"""
        if not latest_record:
            return 0.0

        try:
            date_field = None
            for field in ['end_of_day', 'date', 'period']:
                if field in latest_record:
                    date_field = field
                    break

            if not date_field:
                return 0.0

            latest_date = pd.to_datetime(latest_record[date_field])
            current_date = pd.Timestamp.now()
            days_old = (current_date - latest_date).days

            # 新鮮度評分 (越新越高)
            if days_old <= 1:
                return 1.0
            elif days_old <= 7:
                return 0.8
            elif days_old <= 30:
                return 0.6
            elif days_old <= 90:
                return 0.4
            else:
                return 0.2

        except Exception:
            return 0.0

    def _analyze_market_regimes(self, adaptive_results: Dict[str, Any]) -> Dict[str, Any]:
        """分析市場狀況分佈"""
        regime_analysis = {
            "consensus_regime": adaptive_results.get("consensus_market_state", {}).get("regime", "unknown"),
            "regime_distribution": {},
            "confidence_level": adaptive_results.get("consensus_market_state", {}).get("confidence", 0),
            "source_regime_agreement": 0
        }

        source_analyses = adaptive_results.get("source_analyses", {})
        regime_counts = {}

        for source_name, analysis in source_analyses.items():
            regime = analysis.get("market_state", {}).get("regime", "unknown")
            regime_counts[regime] = regime_counts.get(regime, 0) + 1

        regime_analysis["regime_distribution"] = regime_counts

        # 計算regime同意度
        if regime_counts:
            most_common_regime = max(regime_counts, key=regime_counts.get)
            agreement = regime_counts[most_common_regime] / len(source_analyses)
            regime_analysis["source_regime_agreement"] = agreement

        return regime_analysis

    def _generate_recommendations(self, adaptive_results: Dict[str, Any],
                                comparison_results: Dict[str, Any]) -> List[str]:
        """生成建議"""
        recommendations = []

        # 基於性能比較的建議
        avg_improvement = comparison_results.get("average_improvement", 0)
        if avg_improvement > 10:
            recommendations.append("適應性系統顯著優於傳統方法，建議全面採用")
        elif avg_improvement > 0:
            recommendations.append("適應性系統略有改進，可在關鍵場景使用")
        else:
            recommendations.append("建議優化適應性參數配置")

        # 基於市場狀況的建議
        consensus_regime = adaptive_results.get("consensus_market_state", {}).get("regime", "")
        if consensus_regime == "high_volatility":
            recommendations.append("當前高波動環境，建議使用適應性系統管理風險")
        elif consensus_regime == "bull_market":
            recommendations.append("牛市環境，適應性系統可捕捉更多機會")
        elif consensus_regime == "bear_market":
            recommendations.append("熊市環境，適應性系統提供更好保護")

        # 基於信號信心度的建議
        signal_confidence = adaptive_results.get("final_signal", {}).get("confidence", 0)
        if signal_confidence > 0.7:
            recommendations.append("當前信號信心度高，適合執行交易策略")
        elif signal_confidence < 0.4:
            recommendations.append("信號信心度較低，建議等待更明確的信號")

        return recommendations

    def _save_test_results(self, report: Dict[str, Any]) -> str:
        """保存測試結果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"adaptive_hkma_integration_test_{timestamp}.json"
        filepath = f"C:\\Users\\Penguin8n\\CODEX--\\simplified_system\\results\\{filename}"

        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"📁 測試結果已保存至: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ 保存測試結果失敗: {e}")
            return ""

    def _display_results_summary(self, report: Dict[str, Any]):
        """顯示結果摘要"""
        print("\n" + "=" * 60)
        print("📊 適應性HKMA集成測試結果摘要")
        print("=" * 60)

        # 基本統計
        test_info = report.get("test_info", {})
        print(f"🔍 測試數據源數量: {test_info.get('data_sources_count', 0)}")
        print(f"✅ 成功分析數量: {test_info.get('successful_analysis', 0)}")

        # 適應性分析結果
        adaptive_results = report.get("adaptive_analysis", {})
        final_signal = adaptive_results.get("final_signal", {})
        print(f"\n🎯 最終交易信號: {final_signal.get('signal', 'N/A')}")
        print(f"📈 信號信心度: {final_signal.get('confidence', 0):.2%}")

        market_state = adaptive_results.get("consensus_market_state", {})
        print(f"📊 市場狀況: {market_state.get('regime', 'N/A')}")
        print(f"📉 波動水平: {market_state.get('volatility_level', 0):.4f}")

        # 性能比較
        comparison = report.get("performance_comparison", {})
        avg_improvement = comparison.get("average_improvement", 0)
        comparison_count = comparison.get("comparison_count", 0)
        print(f"\n🔄 性能比較: 適應性 vs 傳統")
        print(f"📊 平均改進幅度: {avg_improvement:.2f}%")
        print(f"🔢 比較樣本數: {comparison_count}")

        # 市場狀況分析
        regime_analysis = report.get("market_regime_analysis", {})
        print(f"\n📈 市場狀況分析:")
        print(f"🎯 共識狀況: {regime_analysis.get('consensus_regime', 'N/A')}")
        print(f"🤝 來源同意度: {regime_analysis.get('source_regime_agreement', 0):.2%}")

        # 建議
        recommendations = report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 系統建議:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")

        print("\n" + "=" * 60)

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """創建錯誤結果"""
        return {
            "test_info": {
                "test_type": "adaptive_hkma_integration",
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            },
            "error": error_message,
            "adaptive_analysis": {},
            "performance_comparison": {},
            "recommendations": ["請檢查數據源連接和系統配置"]
        }

if __name__ == "__main__":
    print("🚀 啟動適應性HKMA系統集成測試")
    print("=" * 60)

    # 創建測試實例
    test = AdaptiveHKMAIntegrationTest()

    # 運行完整測試
    results = test.run_comprehensive_test()

    print("\n🎉 測試完成!")
    print("=" * 60)