#!/usr / bin / env python3
"""
改進的真實數據集成系統
Improved Real Data Integration System

解決測試中發現的問題，完善真實政府數據集成
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# Import system modules
from src.api.government_data import GovernmentDataAPI
from src.api.stock_api import get_hk_stock_data
from unified_data_architecture_standard import (
    DataSourceType,
    UnifiedDataArchitectureStandard,
)

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ImprovedRealDataIntegration:
    """改進的真實數據集成系統"""

    def __init__(self):
        self.government_api = GovernmentDataAPI()
        self.data_standardizer = UnifiedDataArchitectureStandard()
        self.cache = {}
        self.data_quality_reports = {}

    def load_local_government_data(self) -> Dict[str, Any]:
        """加載本地真實政府數據"""
        logger.info("加載本地真實政府數據...")

        local_data = {
            "hibor_rates": None,
            "exchange_rates": None,
            "monetary_base": None,
            "interbank_liquidity": None,
            "efbn_indicative": None,
        }

        data_dir = Path("data / government")

        # 加載各類數據
        data_files = {
            "hibor_rates": list(data_dir.glob("hibor_rates_*.json")),
            "exchange_rates": list(data_dir.glob("exchange_rates_*.json")),
            "monetary_base": list(data_dir.glob("*monetary*.json")),
            "interbank_liquidity": list(data_dir.glob("*interbank*.json")),
            "efbn_indicative": list(data_dir.glob("*efbn*.json")),
        }

        for data_type, files in data_files.items():
            if files:
                # 使用最新的文件
                latest_file = max(files, key = lambda f: f.stat().st_mtime)
                try:
                    with open(latest_file, "r", encoding="utf - 8") as f:
                        data = json.load(f)

                    if "data" in data and data["data"]:
                        local_data[data_type] = data
                        logger.info(f"成功加載 {data_type}: {len(data['data'])} 條記錄")
                    else:
                        logger.warning(f"{data_type} 數據為空")

                except Exception as e:
                    logger.error(f"加載 {data_type} 失敗: {e}")

        return local_data

    def create_alpha_signals_with_real_data(
        self, symbol: str = "0700.HK", days_back: int = 60
    ) -> Dict[str, Any]:
        """使用真實數據創建Alpha信號"""
        logger.info(f"創建 {symbol} 的Alpha信號，使用 {days_back} 天數據...")

        alpha_result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "data_sources_used": [],
            "signals": {},
            "performance_metrics": {},
            "quality_score": 0,
        }

        try:
            # 1. 獲取股票數據
            logger.info("獲取股票數據...")
            stock_data = get_hk_stock_data(symbol, days_back)

            if stock_data is None or len(stock_data) == 0:
                logger.error("無法獲取股票數據")
                return alpha_result

            alpha_result["data_sources_used"].append(
                f"stock_data: {len(stock_data)} records"
            )

            # 2. 加載本地政府數據
            logger.info("加載本地政府數據...")
            local_gov_data = self.load_local_government_data()

            # 統計可用的政府數據
            available_data = {k: v for k, v in local_gov_data.items() if v is not None}
            for data_type, data in available_data.items():
                alpha_result["data_sources_used"].append(
                    f"{data_type}: {len(data['data'])} records"
                )

            logger.info(f"可用政府數據源: {list(available_data.keys())}")

            # 3. 生成技術分析信號
            tech_signals = self._generate_technical_signals(stock_data)
            alpha_result["signals"]["technical"] = tech_signals

            # 4. 生成宏觀經濟信號（基於真實政府數據）
            macro_signals = self._generate_macro_signals(available_data, stock_data)
            alpha_result["signals"]["macro"] = macro_signals

            # 5. 生成綜合Alpha信號
            composite_signals = self._generate_composite_signals(
                tech_signals, macro_signals, stock_data
            )
            alpha_result["signals"]["composite"] = composite_signals

            # 6. 計算性能指標
            performance = self._calculate_signal_performance(
                alpha_result["signals"], stock_data
            )
            alpha_result["performance_metrics"] = performance

            # 7. 計算質量評分
            quality_score = self._calculate_quality_score(alpha_result)
            alpha_result["quality_score"] = quality_score

            logger.info(f"Alpha信號生成完成，質量評分: {quality_score:.2f}")

        except Exception as e:
            logger.error(f"Alpha信號生成失敗: {e}")
            alpha_result["error"] = str(e)

        return alpha_result

    def _generate_technical_signals(self, stock_data: pd.DataFrame) -> Dict[str, Any]:
        """生成技術分析信號"""
        signals = {}

        if len(stock_data) < 20:
            return signals

        close_prices = stock_data["close"]

        # RSI信號
        rsi = self._calculate_rsi(close_prices, 14)
        if rsi is not None:
            signals["rsi"] = {
                "value": rsi,
                "signal": (
                    "OVERSOLD" if rsi < 30 else "OVERBOUGHT" if rsi > 70 else "NEUTRAL"
                ),
                "confidence": self._calculate_rsi_confidence(rsi),
                "weight": 0.25,
            }

        # 移動平均線信號
        sma_short = close_prices.rolling(window = 10).mean()
        sma_long = close_prices.rolling(window = 30).mean()

        if not sma_short.empty and not sma_long.empty:
            latest_short = sma_short.iloc[-1]
            latest_long = sma_long.iloc[-1]
            latest_price = close_prices.iloc[-1]

            ma_signal = "BULLISH" if latest_short > latest_long else "BEARISH"
            ma_strength = abs(latest_short - latest_long) / latest_long * 100

            signals["moving_average"] = {
                "signal": ma_signal,
                "strength": ma_strength,
                "price_vs_ma10": (latest_price - latest_short) / latest_short * 100,
                "price_vs_ma30": (latest_price - latest_long) / latest_long * 100,
                "weight": 0.20,
            }

        # 價格動量信號
        momentum_5d = (
            (close_prices.iloc[-1] / close_prices.iloc[-5] - 1) * 100
            if len(close_prices) >= 5
            else 0
        )
        momentum_20d = (
            (close_prices.iloc[-1] / close_prices.iloc[-20] - 1) * 100
            if len(close_prices) >= 20
            else 0
        )

        signals["momentum"] = {
            "momentum_5d": momentum_5d,
            "momentum_20d": momentum_20d,
            "signal": "STRONG_MOMENTUM" if abs(momentum_5d) > 3 else "WEAK_MOMENTUM",
            "trend": (
                "BULLISH"
                if momentum_20d > 5
                else "BEARISH" if momentum_20d < -5 else "SIDEWAYS"
            ),
            "weight": 0.15,
        }

        # 波動率信號
        returns = close_prices.pct_change().dropna()
        volatility = (
            returns.rolling(window = 20).std().iloc[-1] * np.sqrt(252) * 100
            if len(returns) >= 20
            else 0
        )

        signals["volatility"] = {
            "annualized_volatility": volatility,
            "signal": (
                "HIGH_VOLATILITY"
                if volatility > 30
                else "LOW_VOLATILITY" if volatility < 15 else "NORMAL_VOLATILITY"
            ),
            "recent_volatility": (
                returns.tail(5).std() * np.sqrt(252) * 100
                if len(returns.tail(5)) >= 5
                else 0
            ),
            "weight": 0.10,
        }

        return signals

    def _generate_macro_signals(
        self, government_data: Dict[str, Any], stock_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """生成宏觀經濟信號（基於真實政府數據）"""
        signals = {}

        # HIBOR信號
        if "hibor_rates" in government_data and government_data["hibor_rates"]:
            hibor_data = government_data["hibor_rates"]["data"]
            if hibor_data:
                latest_hibor = hibor_data[0]
                hibor_overnight = latest_hibor.get("hibor_overnight", 0)
                hibor_1m = latest_hibor.get("ir_1m", 0)

                # HIBOR水平信號
                rate_level_signal = (
                    "ACCOMMODATIVE"
                    if hibor_overnight < 3.5
                    else "RESTRICTIVE" if hibor_overnight > 5.0 else "NEUTRAL"
                )

                # HIBOR變化信號
                rate_change_signal = "NEUTRAL"
                if len(hibor_data) > 1:
                    prev_hibor = hibor_data[1].get("hibor_overnight", hibor_overnight)
                    rate_change = hibor_overnight - prev_hibor
                    if rate_change > 0.1:
                        rate_change_signal = "TIGHTENING"
                    elif rate_change < -0.1:
                        rate_change_signal = "EASING"

                signals["hibor"] = {
                    "overnight_rate": hibor_overnight,
                    "one_month_rate": hibor_1m,
                    "level_signal": rate_level_signal,
                    "change_signal": rate_change_signal,
                    "rate_impact": self._assess_rate_impact(hibor_overnight),
                    "weight": 0.25,
                }

        # 匯率信號
        if "exchange_rates" in government_data and government_data["exchange_rates"]:
            exchange_data = government_data["exchange_rates"]["data"]
            if exchange_data:
                latest_fx = exchange_data[0]
                usd_hkd = latest_fx.get("usd_hkd", 7.8)

                # 匯率穩定性信號
                fx_stability = "STABLE" if abs(usd_hkd - 7.8) < 0.05 else "VOLATILE"

                signals["exchange_rate"] = {
                    "usd_hkd": usd_hkd,
                    "stability_signal": fx_stability,
                    "deviation_from_peg": abs(usd_hkd - 7.8),
                    "weight": 0.15,
                }

        # 銀行流動性信號
        if (
            "interbank_liquidity" in government_data
            and government_data["interbank_liquidity"]
        ):
            liquidity_data = government_data["interbank_liquidity"]["data"]
            if liquidity_data:
                latest_liquidity = liquidity_data[0]

                # 提取流動性指標
                liquidity_amount = latest_liquidity.get("amount", 0)

                signals["liquidity"] = {
                    "liquidity_level": liquidity_amount,
                    "signal": (
                        "AMPLE"
                        if liquidity_amount > 1000
                        else "TIGHT" if liquidity_amount < 500 else "NORMAL"
                    ),
                    "weight": 0.20,
                }

        return signals

    def _generate_composite_signals(
        self, tech_signals: Dict, macro_signals: Dict, stock_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """生成綜合Alpha信號"""
        composite = {
            "overall_signal": "NEUTRAL",
            "signal_strength": 0,
            "confidence": 0,
            "component_weights": {},
            "alpha_score": 0,
        }

        try:
            # 計算加權信號
            total_weight = 0
            weighted_signal = 0

            # 技術信號貢獻
            tech_contribution = 0
            tech_weight = 0
            for signal_name, signal_data in tech_signals.items():
                if "weight" in signal_data:
                    signal_score = self._signal_to_numeric(
                        signal_data.get("signal", "NEUTRAL")
                    )
                    tech_contribution += signal_score * signal_data["weight"]
                    tech_weight += signal_data["weight"]

            if tech_weight > 0:
                tech_contribution /= tech_weight
                weighted_signal += tech_contribution * 0.6  # 技術信號權重60%
                total_weight += 0.6
                composite["component_weights"]["technical"] = 0.6

            # 宏觀信號貢獻
            macro_contribution = 0
            macro_weight = 0
            for signal_name, signal_data in macro_signals.items():
                if "weight" in signal_data:
                    signal_score = self._macro_signal_to_numeric(
                        signal_data, signal_name
                    )
                    macro_contribution += signal_score * signal_data["weight"]
                    macro_weight += signal_data["weight"]

            if macro_weight > 0:
                macro_contribution /= macro_weight
                weighted_signal += macro_contribution * 0.4  # 宏觀信號權重40%
                total_weight += 0.4
                composite["component_weights"]["macro"] = 0.4

            # 計算最終信號
            if total_weight > 0:
                final_score = weighted_signal / total_weight

                # 轉換為信號文字
                if final_score > 0.3:
                    composite["overall_signal"] = "STRONG_BUY"
                elif final_score > 0.1:
                    composite["overall_signal"] = "BUY"
                elif final_score > -0.1:
                    composite["overall_signal"] = "HOLD"
                elif final_score > -0.3:
                    composite["overall_signal"] = "SELL"
                else:
                    composite["overall_signal"] = "STRONG_SELL"

                composite["signal_strength"] = abs(final_score)
                composite["alpha_score"] = final_score

            # 計算信心度
            data_count = len(tech_signals) + len(macro_signals)
            composite["confidence"] = min(1.0, data_count / 5.0)  # 最多5個信號來源

        except Exception as e:
            logger.error(f"綜合信號生成錯誤: {e}")

        return composite

    def _signal_to_numeric(self, signal: str) -> float:
        """將信號轉換為數值"""
        signal_map = {
            "STRONG_BUY": 1.0,
            "BUY": 0.5,
            "BULLISH": 0.4,
            "OVERBOUGHT": -0.2,
            "OVERSOLD": 0.3,
            "NEUTRAL": 0,
            "SELL": -0.5,
            "STRONG_SELL": -1.0,
            "BEARISH": -0.4,
        }
        return signal_map.get(signal.upper(), 0)

    def _macro_signal_to_numeric(self, signal_data: Dict, signal_type: str) -> float:
        """將宏觀信號轉換為數值"""
        if signal_type == "hibor":
            signal = signal_data.get("level_signal", "NEUTRAL")
            if signal == "ACCOMMODATIVE":
                return 0.4
            elif signal == "RESTRICTIVE":
                return -0.3
            else:
                return 0

        elif signal_type == "exchange_rate":
            stability = signal_data.get("stability_signal", "STABLE")
            return 0.2 if stability == "STABLE" else -0.1

        elif signal_type == "liquidity":
            signal = signal_data.get("signal", "NORMAL")
            if signal == "AMPLE":
                return 0.3
            elif signal == "TIGHT":
                return -0.2
            else:
                return 0

        return 0

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """計算RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window = period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window = period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi.iloc[-1] if not rsi.empty else None
        except Exception:
            return None

    def _calculate_rsi_confidence(self, rsi: float) -> float:
        """計算RSI信心度"""
        if rsi is None:
            return 0

        # 極值區域信心度更高
        if rsi < 20 or rsi > 80:
            return 0.9
        elif rsi < 30 or rsi > 70:
            return 0.7
        else:
            return 0.4

    def _assess_rate_impact(self, hibor_rate: float) -> str:
        """評估利率影響"""
        if hibor_rate < 3.0:
            return "ACCOMMODATIVE_POSITIVE"
        elif hibor_rate > 5.0:
            return "RESTRICTIVE_NEGATIVE"
        else:
            return "NEUTRAL"

    def _calculate_signal_performance(
        self, signals: Dict, stock_data: pd.DataFrame
    ) -> Dict:
        """計算信號性能指標"""
        performance = {
            "signal_count": 0,
            "data_source_diversity": 0,
            "signal_consistency": 0,
            "expected_alpha": 0,
        }

        try:
            # 計算信號數量
            tech_count = len(signals.get("technical", {}))
            macro_count = len(signals.get("macro", {}))
            performance["signal_count"] = tech_count + macro_count

            # 數據源多樣性
            performance["data_source_diversity"] = min(
                1.0, performance["signal_count"] / 5.0
            )

            # 計算預期Alpha（基於信號強度和信心度）
            composite = signals.get("composite", {})
            if composite:
                performance["signal_consistency"] = composite.get("confidence", 0)
                performance["expected_alpha"] = (
                    composite.get("alpha_score", 0) * 0.15
                )  # 年化預期回報

        except Exception as e:
            logger.error(f"性能計算錯誤: {e}")

        return performance

    def _calculate_quality_score(self, alpha_result: Dict) -> float:
        """計算Alpha信號質量評分"""
        score = 0

        try:
            # 數據源多樣性 (30%)
            data_sources = alpha_result.get("data_sources_used", [])
            diversity_score = min(1.0, len(data_sources) / 4.0)
            score += diversity_score * 0.3

            # 信號質量 (40%)
            signals = alpha_result.get("signals", {})
            signal_quality = 0
            if signals.get("technical"):
                signal_quality += 0.5
            if signals.get("macro"):
                signal_quality += 0.5
            score += signal_quality * 0.4

            # 性能指標 (30%)
            performance = alpha_result.get("performance_metrics", {})
            performance_score = performance.get("signal_consistency", 0)
            score += performance_score * 0.3

        except Exception as e:
            logger.error(f"質量評分計算錯誤: {e}")

        return min(1.0, max(0, score))

    def run_comprehensive_analysis(self, symbols: List[str] = None) -> Dict[str, Any]:
        """運行綜合分析"""
        if symbols is None:
            symbols = ["0700.HK", "0941.HK", "1398.HK"]

        logger.info(f"開始綜合分析，股票: {symbols}")

        analysis_results = {
            "analysis_session": {
                "timestamp": datetime.now().isoformat(),
                "symbols_analyzed": symbols,
                "analysis_type": "real_data_alpha_integration",
            },
            "individual_results": {},
            "comparative_analysis": {},
            "portfolio_signals": {},
            "quality_summary": {},
        }

        try:
            # 個股分析
            for symbol in symbols:
                logger.info(f"分析 {symbol}...")
                result = self.create_alpha_signals_with_real_data(symbol, 60)
                analysis_results["individual_results"][symbol] = result

            # 比較分析
            analysis_results["comparative_analysis"] = (
                self._perform_comparative_analysis(
                    analysis_results["individual_results"]
                )
            )

            # 投資組合信號
            analysis_results["portfolio_signals"] = self._generate_portfolio_signals(
                analysis_results["individual_results"]
            )

            # 質量摘要
            analysis_results["quality_summary"] = self._generate_quality_summary(
                analysis_results["individual_results"]
            )

            # 保存結果
            self._save_analysis_results(analysis_results)

        except Exception as e:
            logger.error(f"綜合分析失敗: {e}")
            analysis_results["error"] = str(e)

        return analysis_results

    def _perform_comparative_analysis(self, individual_results: Dict) -> Dict:
        """執行比較分析"""
        comparison = {
            "best_alpha_source": None,
            "highest_quality": None,
            "signal_diversity": {},
            "performance_ranking": [],
        }

        try:
            scores = {}
            for symbol, result in individual_results.items():
                quality = result.get("quality_score", 0)
                scores[symbol] = quality

            if scores:
                # 最高質量股票
                best_symbol = max(scores, key = scores.get)
                comparison["highest_quality"] = {
                    "symbol": best_symbol,
                    "quality_score": scores[best_symbol],
                    "alpha_signals": individual_results[best_symbol].get("signals", {}),
                }

                # 性能排名
                ranked_symbols = sorted(
                    scores.items(), key = lambda x: x[1], reverse = True
                )
                comparison["performance_ranking"] = [
                    {"symbol": symbol, "quality_score": score}
                    for symbol, score in ranked_symbols
                ]

        except Exception as e:
            logger.error(f"比較分析錯誤: {e}")

        return comparison

    def _generate_portfolio_signals(self, individual_results: Dict) -> Dict:
        """生成投資組合信號"""
        portfolio = {
            "overall_recommendation": "HOLD",
            "top_picks": [],
            "allocation_weights": {},
            "risk_assessment": "MEDIUM",
        }

        try:
            quality_scores = {}
            for symbol, result in individual_results.items():
                quality_scores[symbol] = result.get("quality_score", 0)

            if quality_scores:
                # 找出頂級推薦
                avg_quality = np.mean(list(quality_scores.values()))
                top_picks = [
                    symbol
                    for symbol, score in quality_scores.items()
                    if score > avg_quality * 1.1
                ]
                portfolio["top_picks"] = top_picks

                # 分配權重（基於質量評分）
                total_score = sum(quality_scores.values())
                if total_score > 0:
                    for symbol, score in quality_scores.items():
                        portfolio["allocation_weights"][symbol] = score / total_score

                # 整體建議
                if avg_quality > 0.7:
                    portfolio["overall_recommendation"] = "BULLISH"
                elif avg_quality < 0.3:
                    portfolio["overall_recommendation"] = "BEARISH"

        except Exception as e:
            logger.error(f"投資組合信號生成錯誤: {e}")

        return portfolio

    def _generate_quality_summary(self, individual_results: Dict) -> Dict:
        """生成質量摘要"""
        summary = {
            "total_symbols": len(individual_results),
            "average_quality": 0,
            "quality_distribution": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "data_source_coverage": {},
            "integration_status": "SUCCESS",
        }

        try:
            qualities = []
            data_source_counts = {}

            for symbol, result in individual_results.items():
                quality = result.get("quality_score", 0)
                qualities.append(quality)

                # 質量分類
                if quality > 0.7:
                    summary["quality_distribution"]["HIGH"] += 1
                elif quality > 0.4:
                    summary["quality_distribution"]["MEDIUM"] += 1
                else:
                    summary["quality_distribution"]["LOW"] += 1

                # 數據源統計
                data_sources = result.get("data_sources_used", [])
                for source in data_sources:
                    data_source_counts[source] = data_source_counts.get(source, 0) + 1

            if qualities:
                summary["average_quality"] = np.mean(qualities)

            summary["data_source_coverage"] = data_source_counts

        except Exception as e:
            logger.error(f"質量摘要生成錯誤: {e}")

        return summary

    def _save_analysis_results(self, results: Dict):
        """保存分析結果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"improved_real_data_analysis_{timestamp}.json"

            with open(filename, "w", encoding="utf - 8") as f:
                json.dump(results, f, indent = 2, ensure_ascii = False, default = str)

            logger.info(f"分析結果已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存分析結果失敗: {e}")


def main():
    """主函數"""
    print("啟動改進的真實數據集成系統...")
    print("=" * 60)

    # 創建集成系統
    integration_system = ImprovedRealDataIntegration()

    # 運行綜合分析
    symbols = ["0700.HK", "0941.HK", "1398.HK"]
    results = integration_system.run_comprehensive_analysis(symbols)

    # 顯示結果摘要
    print("\n" + "=" * 60)
    print("分析結果摘要")
    print("=" * 60)

    session = results["analysis_session"]
    print(f"分析時間: {session['timestamp']}")
    print(f"分析股票: {', '.join(session['symbols_analyzed'])}")

    # 質量摘要
    quality_summary = results.get("quality_summary", {})
    print(f"\n質量評分:")
    print(f"  總股票數: {quality_summary.get('total_symbols', 0)}")
    print(f"  平均質量: {quality_summary.get('average_quality', 0):.3f}")
    print(f"  高質量: {quality_summary['quality_distribution']['HIGH']}")
    print(f"  中質量: {quality_summary['quality_distribution']['MEDIUM']}")
    print(f"  低質量: {quality_summary['quality_distribution']['LOW']}")

    # 投資組合建議
    portfolio = results.get("portfolio_signals", {})
    print(f"\n投資組合建議:")
    print(f"  整體建議: {portfolio.get('overall_recommendation', 'HOLD')}")
    print(f"  頂級推薦: {', '.join(portfolio.get('top_picks', []))}")
    print(f"  風險評估: {portfolio.get('risk_assessment', 'MEDIUM')}")

    # 最佳表現股票
    comparison = results.get("comparative_analysis", {})
    if comparison.get("highest_quality"):
        best = comparison["highest_quality"]
        print(f"\n最佳表現股票:")
        print(f"  股票: {best['symbol']}")
        print(f"  質量評分: {best['quality_score']:.3f}")

    # 個股結果簡要
    print(f"\n個股分析結果:")
    for symbol, result in results.get("individual_results", {}).items():
        quality = result.get("quality_score", 0)
        data_sources = len(result.get("data_sources_used", []))
        print(f"  {symbol}: 質量 {quality:.3f}, 數據源 {data_sources} 個")

    print("\n" + "=" * 60)
    print("分析完成！")

    return results


if __name__ == "__main__":
    analysis_results = main()
