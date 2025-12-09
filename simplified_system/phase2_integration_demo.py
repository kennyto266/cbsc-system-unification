#!/usr/bin/env python3
"""
第二階段整合演示腳本 - Phase 2 Integration Demo Script
展示所有香港市場深化模塊的整合應用
Demonstrating the integrated application of all Hong Kong market deepening modules
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import numpy as np
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our Phase 2 modules
from src.risk.hk_risk_factors import HKRiskFactorCalculator
from src.market.hk_microstructure import HKMarketMicrostructureAnalyzer
from src.risk.weather_disruption_modeler import HKWeatherDisruptionModeler, get_weather_modeler
from src.market.mainland_capital_flow_detector import MainlandCapitalFlowAnalyzer, get_mainland_capital_flow_detector
from src.data.hk_market_data_manager import get_hk_market_data_manager

class HKMarketPhase2Integration:
    """香港市場第二階段整合系統"""

    def __init__(self):
        self.risk_calculator = HKRiskFactorCalculator()
        self.microstructure_analyzer = HKMarketMicrostructureAnalyzer("0700.HK")
        self.weather_modeler = get_weather_modeler()
        self.capital_flow_detector = get_mainland_capital_flow_detector()
        self.market_data_manager = get_hk_market_data_manager()

    async def generate_comprehensive_market_analysis(self) -> Dict[str, Any]:
        """生成綜合市場分析報告"""
        logger.info("開始生成香港市場綜合分析報告...")

        start_time = time.time()

        try:
            # 1. 獲取市場數據
            logger.info("1/6 - 獲取市場基礎數據...")
            market_data = await self._get_market_data()

            # 2. 計算香港專用風險因子
            logger.info("2/6 - 計算香港專用風險因子...")
            risk_analysis = await self._analyze_hk_risk_factors(market_data)

            # 3. 分析市場微結構
            logger.info("3/6 - 分析市場微結構...")
            microstructure_analysis = await self._analyze_market_microstructure()

            # 4. 評估天氣干擾影響
            logger.info("4/6 - 評估天氣干擾影響...")
            weather_impact = await self._assess_weather_disruption()

            # 5. 檢測內地資金流動
            logger.info("5/6 - 檢測內地資金流動...")
            capital_flow_analysis = await self._detect_capital_flows()

            # 6. 整合所有分析結果
            logger.info("6/6 - 整合分析結果...")
            integrated_analysis = self._integrate_analyses(
                market_data, risk_analysis, microstructure_analysis,
                weather_impact, capital_flow_analysis
            )

            processing_time = time.time() - start_time

            # 生成最終報告
            final_report = {
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": round(processing_time, 2),
                "market_overview": {
                    "hsi_level": "根據最新數據計算",
                    "market_status": "正常交易",
                    "analysis_modules_used": 6
                },
                "market_data": market_data,
                "risk_analysis": risk_analysis,
                "microstructure_analysis": microstructure_analysis,
                "weather_disruption": weather_impact,
                "capital_flows": capital_flow_analysis,
                "integrated_insights": integrated_analysis,
                "recommendations": self._generate_comprehensive_recommendations(integrated_analysis),
                "risk_alerts": self._generate_risk_alerts(integrated_analysis)
            }

            logger.info(f"分析完成！耗時 {processing_time:.2f} 秒")
            return final_report

        except Exception as e:
            logger.error(f"綜合分析過程中發生錯誤: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def _get_market_data(self) -> Dict[str, Any]:
        """獲取市場基礎數據"""
        try:
            # 獲取恆生指數成分股數據
            hsi_symbols = await self.market_data_manager.get_hsi_constituents_data()

            # 獲取主要股票的市場數據
            sample_symbols = hsi_symbols[:10]  # 取前10個
            stock_data = await self.market_data_manager.get_hk_stock_data(sample_symbols)

            # 獲取香港金管局經濟數據
            hibor_data = await self.market_data_manager.get_hkma_economic_data("hibor")
            monetary_data = await self.market_data_manager.get_hkma_economic_data("monetary")
            exchange_data = await self.market_data_manager.get_hkma_economic_data("exchange")

            return {
                "hsi_constituents_count": len(hsi_symbols),
                "sample_symbols_analyzed": len(stock_data),
                "market_data_quality": "良好" if len(stock_data) >= 8 else "需改善",
                "economic_indicators": {
                    "hibor_rate": hibor_data.get("value"),
                    "monetary_base": monetary_data.get("value"),
                    "exchange_rate": exchange_data.get("value")
                },
                "data_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"獲取市場數據失敗: {e}")
            return {"error": str(e)}

    async def _analyze_hk_risk_factors(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析香港專用風險因子"""
        try:
            # 模擬市場參數（實際應用中從真實數據獲取）
            market_params = {
                'hibor_rate': market_data.get('economic_indicators', {}).get('hibor_rate', 3.5) / 100,
                'southbound_flow': np.random.normal(15, 5),  # 億港元
                'hk_risk_premium': 0.025,
                'volatility_index': np.random.normal(20, 5),
                'currency_peg_pressure': 0.1
            }

            # 計算各種風險因子
            currency_peg_risk = self.risk_calculator.calculate_currency_peg_risk(
                market_params['hibor_rate'],
                market_params.get('economic_indicators', {}).get('exchange_rate', 7.8)
            )

            southbound_flow_risk = self.risk_calculator.calculate_southbound_flow_risk(
                market_params['southbound_flow']
            )

            weather_risk = self.risk_calculator.calculate_weather_disruption_risk()
            policy_risk = self.risk_calculator.calculate_policy_regulation_risk()

            # 綜合風險評分
            risk_scores = {
                'currency_peg': currency_peg_risk['risk_score'],
                'southbound_flow': southbound_flow_risk['risk_score'],
                'weather_disruption': weather_risk['risk_score'],
                'policy_regulation': policy_risk['risk_score']
            }

            overall_risk = np.mean(list(risk_scores.values()))

            return {
                "individual_risk_factors": {
                    "currency_peg": currency_peg_risk,
                    "southbound_flow": southbound_flow_risk,
                    "weather_disruption": weather_risk,
                    "policy_regulation": policy_risk
                },
                "risk_scores": risk_scores,
                "overall_risk_score": round(overall_risk, 3),
                "risk_level": self._get_risk_level(overall_risk),
                "market_stability": "穩定" if overall_risk < 0.3 else "波動" if overall_risk < 0.6 else "高風險"
            }

        except Exception as e:
            logger.error(f"風險因子分析失敗: {e}")
            return {"error": str(e)}

    async def _analyze_market_microstructure(self) -> Dict[str, Any]:
        """分析市場微結構"""
        try:
            # 模擬添加一些交易數據
            self._simulate_trading_data()

            # 計算流動性指標
            liquidity_measures = self.microstructure_analyzer.calculate_liquidity_measures()

            # 分析競價動態
            auction_dynamics = self.microstructure_analyzer.analyze_auction_dynamics()

            # 檢測市場莊家
            market_makers = self.microstructure_analyzer.detect_market_makers()

            # 分析交易時段模式
            session_analyzer = HKMarketMicrostructureAnalyzer.session_analyzer_class()
            session_patterns = session_analyzer.analyze_session_patterns(self.microstructure_analyzer.trades)

            return {
                "liquidity_analysis": liquidity_measures,
                "auction_dynamics": auction_dynamics,
                "market_maker_activity": market_makers,
                "trading_session_patterns": session_patterns,
                "market_efficiency": self._assess_market_efficiency(liquidity_measures),
                "trading_activity_level": "活躍" if liquidity_measures.get('trading_volume_24h', 0) > 1000000 else "正常"
            }

        except Exception as e:
            logger.error(f"市場微結構分析失敗: {e}")
            return {"error": str(e)}

    def _simulate_trading_data(self):
        """模擬交易數據（用於演示）"""
        # 這裡添加一些模擬交易數據來支持微結構分析
        pass  # 在實際應用中，這裡會填充真實的交易數據

    def _assess_market_efficiency(self, liquidity_measures: Dict[str, float]) -> str:
        """評估市場效率"""
        if not liquidity_measures:
            return "無法評估"

        # 基於流動性指標評估市場效率
        effective_spread = liquidity_measures.get('effective_spread', float('inf'))
        amihud_illiquidity = liquidity_measures.get('amihud_illiquidity', 0)

        if effective_spread < 0.001 and amihud_illiquidity < 0.01:
            return "高效率"
        elif effective_spread < 0.005 and amihud_illiquidity < 0.05:
            return "中等效率"
        else:
            return "低效率"

    async def _assess_weather_disruption(self) -> Dict[str, Any]:
        """評估天氣干擾影響"""
        try:
            # 生成天氣風險報告
            weather_report = await self.weather_modeler.generate_weather_risk_report()

            return {
                "current_weather_events": weather_report.get("current_events", 0),
                "trading_status_impact": weather_report.get("overall_trading_status", "normal"),
                "risk_level": weather_report.get("risk_assessment", {}).get("risk_level", "MINIMAL"),
                "volatility_impact": weather_report.get("risk_assessment", {}).get("volatility_impact", 0),
                "volume_impact": weather_report.get("risk_assessment", {}).get("volume_impact", 0),
                "sector_impacts": weather_report.get("sector_impacts", {}),
                "operational_recommendations": weather_report.get("recommendations", []),
                "market_operations": {
                    "trading_expected": "正常" if weather_report.get("overall_trading_status") == "normal" else "受影響",
                    "liquidity_concern": "低" if weather_report.get("risk_assessment", {}).get("liquidity_impact", 0) < 0.3 else "高"
                }
            }

        except Exception as e:
            logger.error(f"天氣干擾評估失敗: {e}")
            return {"error": str(e)}

    async def _detect_capital_flows(self) -> Dict[str, Any]:
        """檢測內地資金流動"""
        try:
            # 生成資金流動報告
            flow_report = await self.capital_flow_detector.generate_capital_flow_report()

            return {
                "current_sentiment": flow_report.flow_sentiment.value,
                "net_southbound_flow_billion": round(flow_report.net_flow / 1000000000, 2),
                "flow_intensity": "強勁" if abs(flow_report.net_flow) > 50000000000 else "中等" if abs(flow_report.net_flow) > 10000000000 else "微弱",
                "sector_flow_analysis": {
                    sector: {
                        "net_flow_billion": round(analysis.net_flow_hkd / 1000000000, 2),
                        "intensity": analysis.flow_intensity.value,
                        "momentum_score": round(analysis.momentum_score, 2)
                    }
                    for sector, analysis in flow_report.sector_analyses.items()
                },
                "top_flow_symbols": flow_report.top_flow_symbols[:5],
                "market_impact": flow_report.market_impact_assessment,
                "trend_analysis": flow_report.trend_analysis,
                "risk_indicators": flow_report.risk_indicators,
                "investment_implications": self._generate_investment_implications(flow_report)
            }

        except Exception as e:
            logger.error(f"資金流動檢測失敗: {e}")
            return {"error": str(e)}

    def _generate_investment_implications(self, flow_report) -> List[str]:
        """生成投資含義"""
        implications = []

        sentiment = flow_report.flow_sentiment.value
        net_flow = flow_report.net_flow

        if "bullish" in sentiment:
            implications.append("內地資金情緒樂觀，港股市場獲支撐")
        elif "bearish" in sentiment:
            implications.append("內地資金流出，港股市場面臨壓力")
        else:
            implications.append("資金流向中性，市場走勢需結合其他因素")

        # 行業層面
        top_sector = None
        max_flow = float('-inf')
        for sector, analysis in flow_report.sector_analyses.items():
            if analysis.net_flow_hkd > max_flow:
                max_flow = analysis.net_flow_hkd
                top_sector = sector

        if top_sector:
            implications.append(f"{top_sector}行業獲最多內地資青睞")

        return implications

    def _integrate_analyses(self, market_data, risk_analysis, microstructure_analysis,
                          weather_impact, capital_flow_analysis) -> Dict[str, Any]:
        """整合所有分析結果"""
        try:
            # 風險評級綜合
            risk_level = risk_analysis.get("risk_level", "無法評估")
            weather_risk = weather_impact.get("risk_level", "MINIMAL")
            capital_risk = "HIGH" if len(capital_flow_analysis.get("risk_indicators", [])) > 2 else "MEDIUM"

            # 市場狀況綜合評估
            market_conditions = {
                "liquidity_status": microstructure_analysis.get("market_efficiency", "無法評估"),
                "trading_activity": microstructure_analysis.get("trading_activity_level", "正常"),
                "weather_operations": weather_impact.get("market_operations", {}).get("trading_expected", "正常"),
                "capital_momentum": capital_flow_analysis.get("flow_intensity", "微弱")
            }

            # 整體信心指數
            confidence_score = self._calculate_confidence_score(
                risk_analysis, weather_impact, capital_flow_analysis
            )

            # 關鍵風險因素
            key_risks = []
            if risk_analysis.get("overall_risk_score", 0) > 0.5:
                key_risks.append("高市場風險")
            if weather_risk not in ["MINIMAL", "LOW"]:
                key_risks.append("天氣操作風險")
            if "bearish" in capital_flow_analysis.get("current_sentiment", ""):
                key_risks.append("資金流出壓力")

            return {
                "overall_risk_assessment": {
                    "primary_risk_level": risk_level,
                    "secondary_risks": [weather_risk, capital_risk],
                    "key_risk_factors": key_risks,
                    "confidence_score": confidence_score
                },
                "market_conditions": market_conditions,
                "strategic_recommendations": self._generate_strategic_recommendations(
                    risk_level, weather_impact, capital_flow_analysis
                ),
                "monitoring_priorities": self._identify_monitoring_priorities(
                    risk_analysis, microstructure_analysis, capital_flow_analysis
                )
            }

        except Exception as e:
            logger.error(f"分析整合失敗: {e}")
            return {"error": str(e)}

    def _calculate_confidence_score(self, risk_analysis, weather_impact, capital_flow_analysis) -> float:
        """計算整體信心分數"""
        try:
            # 基於各個分析結果計算信心分數
            risk_score = 1.0 - risk_analysis.get("overall_risk_score", 0.5)

            weather_confidence = 0.8 if weather_impact.get("risk_level") == "MINIMAL" else 0.5

            capital_confidence = 0.8 if "bullish" in capital_flow_analysis.get("current_sentiment", "") else 0.5

            # 加權平均
            confidence_score = (risk_score * 0.4 + weather_confidence * 0.2 + capital_confidence * 0.4)

            return round(confidence_score, 3)

        except:
            return 0.5  # 默認中等信心

    def _generate_strategic_recommendations(self, risk_level, weather_impact, capital_flow_analysis) -> List[str]:
        """生成戰略建議"""
        recommendations = []

        # 基於風險等級的建議
        if risk_level == "HIGH":
            recommendations.append("市場風險較高，建議減少倉位規模，加強風險管理")
        elif risk_level == "MEDIUM":
            recommendations.append("市場風險中等，可維持正常投資策略，但需密切監控")
        else:
            recommendations.append("市場風險較低，可考慮適度增加投資倉位")

        # 基於天氣影響的建議
        if weather_impact.get("trading_status_impact") != "normal":
            recommendations.append("天氣因素影響市場運作，建議使用限價單，注意流動性")

        # 基於資金流動的建議
        if "bullish" in capital_flow_analysis.get("current_sentiment", ""):
            recommendations.append("內地資金流入積極，關注受資青睞的行業和股票")
        elif "bearish" in capital_flow_analysis.get("current_sentiment", ""):
            recommendations.append("內地資金流出壓力，建議謹慎為主，關注防禦性行業")

        return recommendations

    def _identify_monitoring_priorities(self, risk_analysis, microstructure_analysis, capital_flow_analysis) -> List[str]:
        """識別監控重點"""
        priorities = []

        # 風險監控
        if risk_analysis.get("overall_risk_score", 0) > 0.5:
            priorities.append("密切監控市場風險指標變化")

        # 流動性監控
        if microstructure_analysis.get("liquidity_analysis", {}).get("effective_spread", 0) > 0.01:
            priorities.append("監控市場流動性變化")

        # 資金流動監控
        if capital_flow_analysis.get("risk_indicators"):
            priorities.append("重點監控內地資金流向變化")

        # 微觀結構監控
        if len(microstructure_analysis.get("market_maker_activity", {})) > 0:
            priorities.append("監控市場莊家活動動向")

        return priorities

    def _generate_comprehensive_recommendations(self, integrated_analysis: Dict[str, Any]) -> List[str]:
        """生成綜合建議"""
        try:
            recommendations = []

            # 基於信心分數的建議
            confidence_score = integrated_analysis.get("overall_risk_assessment", {}).get("confidence_score", 0.5)

            if confidence_score > 0.7:
                recommendations.append("市場條件良好，可適度積極佈局")
            elif confidence_score > 0.4:
                recommendations.append("市場條件一般，建議均衡配置")
            else:
                recommendations.append("市場條件不確定，建議保守為主")

            # 添加戰略建議
            strategic_recs = integrated_analysis.get("strategic_recommendations", [])
            recommendations.extend(strategic_recs)

            return recommendations

        except Exception as e:
            logger.error(f"生成綜合建議失敗: {e}")
            return ["無法生成具體建議，請謹慎操作"]

    def _generate_risk_alerts(self, integrated_analysis: Dict[str, Any]) -> List[str]:
        """生成風險警報"""
        try:
            alerts = []

            # 關鍵風險因素
            key_risks = integrated_analysis.get("overall_risk_assessment", {}).get("key_risk_factors", [])
            if key_risks:
                alerts.extend([f"⚠️ {risk}" for risk in key_risks])

            # 監控重點
            monitoring_priorities = integrated_analysis.get("monitoring_priorities", [])
            if monitoring_priorities:
                alerts.extend([f"📊 {priority}" for priority in monitoring_priorities])

            return alerts

        except Exception as e:
            logger.error(f"生成風險警報失敗: {e}")
            return ["⚠️ 分析系統異常，請謹慎操作"]

    def _get_risk_level(self, risk_score: float) -> str:
        """根據風險分數確定風險等級"""
        if risk_score >= 0.7:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

async def main():
    """主函數 - 演示第二階段整合系統"""
    print("=" * 60)
    print("香港市場第二階段深化系統整合演示")
    print("Hong Kong Market Phase 2 Deepening System Integration Demo")
    print("=" * 60)
    print()

    # 初始化整合系統
    integration_system = HKMarketPhase2Integration()

    try:
        # 生成綜合分析報告
        comprehensive_report = await integration_system.generate_comprehensive_market_analysis()

        # 顯示關鍵結果
        print("📊 綜合分析報告摘要")
        print("-" * 40)

        if "error" in comprehensive_report:
            print(f"❌ 分析失敗: {comprehensive_report['error']}")
            return

        # 市場概覽
        market_overview = comprehensive_report.get("market_overview", {})
        print(f"分析模塊數量: {market_overview.get('analysis_modules_used', 0)}")
        print(f"處理時間: {comprehensive_report.get('processing_time_seconds', 0):.2f} 秒")

        # 風險分析
        risk_analysis = comprehensive_report.get("risk_analysis", {})
        risk_level = risk_analysis.get("risk_level", "UNKNOWN")
        overall_score = risk_analysis.get("overall_risk_score", 0)
        print(f"市場風險等級: {risk_level} (分數: {overall_score:.3f})")

        # 天氣影響
        weather = comprehensive_report.get("weather_disruption", {})
        weather_risk = weather.get("risk_level", "UNKNOWN")
        trading_status = weather.get("trading_status_impact", "normal")
        print(f"天氣風險等級: {weather_risk}, 交易影響: {trading_status}")

        # 資金流動
        capital_flows = comprehensive_report.get("capital_flows", {})
        flow_sentiment = capital_flows.get("current_sentiment", "UNKNOWN")
        net_flow = capital_flows.get("net_southbound_flow_billion", 0)
        print(f"資金流向情緒: {flow_sentiment}, 淨流入: {net_flow:.2f} 億港元")

        # 綜合建議
        recommendations = comprehensive_report.get("recommendations", [])
        print(f"\n💡 綜合建議 ({len(recommendations)}條):")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

        # 風險警報
        alerts = comprehensive_report.get("risk_alerts", [])
        if alerts:
            print(f"\n⚠️ 風險警報 ({len(alerts)}條):")
            for alert in alerts:
                print(f"  {alert}")

        # 保存完整報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"hk_market_phase2_analysis_{timestamp}.json"
        report_path = Path("analysis_reports") / report_filename

        # 創建目錄
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 完整報告已保存至: {report_path}")

        print("\n" + "=" * 60)
        print("第二階段整合系統演示完成")
        print("Phase 2 Integration System Demo Completed")
        print("=" * 60)

    except Exception as e:
        logger.error(f"演示過程中發生錯誤: {e}")
        print(f"❌ 演示失敗: {e}")

    finally:
        # 清理資源
        try:
            await integration_system.market_data_manager.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())