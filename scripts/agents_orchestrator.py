import asyncio
from typing import Dict, Any, List
from pprint import pprint

from src.data_adapters.data_service import DataService
from src.agents.real_agents.base_real_agent import RealAgentConfig
from scripts.agent_http_pipeline import QAAgentConcrete


# --- Message contracts (simplified) ---
def make_analysis_report(symbol: str, analysis) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "signal_strength": analysis.signal_strength,
        "direction": analysis.signal_direction,
        "confidence": analysis.confidence,
        "insights": analysis.insights[:5] if hasattr(analysis, "insights") else [],
        "warnings": analysis.warnings[:5] if hasattr(analysis, "warnings") else [],
    }


def research_debate(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    # 简版：均值融合 + 乐观/悲观加权（此处等权）
    if not reports:
        return {"decision": "hold", "confidence": 0.0, "rationale": ["no reports"]}
    avg_strength = sum(r.get("signal_strength", 0) for r in reports) / len(reports)
    avg_conf = sum(r.get("confidence", 0) for r in reports) / len(reports)
    # 聚合方向：多数投票（buy/sell/neutral/hold）
    dirs = [r.get("direction", "neutral") for r in reports]
    decision = max(set(dirs), key=dirs.count) if dirs else "hold"
    return {
        "decision": decision,
        "confidence": avg_conf,
        "strength": avg_strength,
        "rationale": [f"votes={dirs}", f"avg_strength={avg_strength:.3f}", f"avg_conf={avg_conf:.3f}"],
    }


def trader_plan(symbol: str, research: Dict[str, Any]) -> Dict[str, Any]:
    dec = research.get("decision", "hold")
    conf = float(research.get("confidence", 0))
    strength = float(research.get("strength", 0))
    side = "buy" if dec == "buy" else "sell" if dec == "sell" else "flat"
    position_size = min(0.1, max(0.0, strength * conf))  # 简化 sizing
    return {
        "symbol": symbol,
        "side": side,
        "size": position_size,
        "target": None,
        "stop": None,
        "est_cost": 0.0005,
        "slippage": 0.0005,
    }


def risk_review(plan: Dict[str, Any]) -> Dict[str, Any]:
    size = float(plan.get("size", 0))
    if size <= 0:
        return {"decision": "reject", "reasons": ["no signal"], "limits": {}}
    if size > 0.08:
        return {"decision": "lower", "reasons": ["size too large"], "limits": {"max_size": 0.08}}
    return {"decision": "approve", "reasons": [], "limits": {}}


async def run_symbol(symbol: str) -> Dict[str, Any]:
    ds = DataService()
    ok = await ds.initialize()
    if not ok:
        return {"error": "dataservice init failed"}

    # 1) pull data
    data = await ds.get_market_data(symbol, source_preference="http_api")
    if not data:
        await ds.cleanup()
        return {"symbol": symbol, "error": "no data"}

    # 2) technical agent
    cfg = RealAgentConfig(
        agent_id=f"qa_orch_{symbol.replace('.','_').lower()}",
        agent_type="quantitative_analyst",
        name=f"QA_ORCH_{symbol}",
        data_sources=["http_api"],
        update_frequency=60,
        lookback_period=60,
        analysis_methods=["technical", "regime"],
        signal_threshold=0.1,
        confidence_threshold=0.1,
        ml_models=[],
        performance_tracking=False,
        backtest_enabled=False,
    )
    agent = QAAgentConcrete(cfg)
    await agent.initialize()
    analysis = await agent.analyze_market_data(data)
    tech_report = make_analysis_report(symbol, analysis)

    # 2b) sentiment/news/fundamental 简版报告（基于价格序列近似推导，占位可替换真实源）
    # 提取基础序列
    # 我们从 data（RealMarketData 列表）中构造简化价格序列
    prices = [float(d.close_price) for d in data]
    def last_pct_change(seq: List[float], n: int = 5) -> float:
        if len(seq) < n + 1:
            return 0.0
        return (seq[-1] / seq[-1 - n] - 1.0)

    # Sentiment: 近5期 vs 近20期的动量差作为情绪代理
    mom5 = last_pct_change(prices, 5)
    mom20 = last_pct_change(prices, 20)
    sent_conf = max(0.0, min(1.0, abs(mom5 - mom20) * 10))
    sent_dir = "buy" if mom5 > mom20 * 1.05 else "sell" if mom5 < mom20 * 0.95 else "neutral"
    sentiment_report = {
        "symbol": symbol,
        "signal_strength": min(1.0, abs(mom5) * 12),
        "direction": sent_dir,
        "confidence": sent_conf,
        "insights": [f"mom5={mom5:.4f}", f"mom20={mom20:.4f}"],
        "warnings": [],
    }

    # News: 占位（无真实新闻源），保持中性、低置信度，可加入波动加权
    vol_proxy = (max(prices[-20:]) - min(prices[-20:])) / prices[-20] if len(prices) > 20 else 0.0
    news_report = {
        "symbol": symbol,
        "signal_strength": min(1.0, vol_proxy),
        "direction": "neutral",
        "confidence": min(0.3, vol_proxy),
        "insights": ["no-news-source"],
        "warnings": [],
    }

    # Fundamental: 占位（无基本面源），根据长期动量给方向但低置信
    long_mom = last_pct_change(prices, 60)
    fund_dir = "buy" if long_mom > 0 else "sell" if long_mom < 0 else "neutral"
    fundamental_report = {
        "symbol": symbol,
        "signal_strength": min(1.0, abs(long_mom) * 8),
        "direction": fund_dir,
        "confidence": 0.25,
        "insights": [f"long_mom={long_mom:.4f}"],
        "warnings": ["placeholder-fundamental"],
    }

    # 3) research debate (此处聚合单报告；可并入 sentiment/news/fundamental 报告)
    research = research_debate([tech_report, sentiment_report, news_report, fundamental_report])

    # 4) trader plan
    plan = trader_plan(symbol, research)

    # 5) risk review
    review = risk_review(plan)

    await agent.cleanup()
    await ds.cleanup()

    return {
        "symbol": symbol,
        "analysis": {
            "technical": tech_report,
            "sentiment": sentiment_report,
            "news": news_report,
            "fundamental": fundamental_report,
        },
        "research": research,
        "trade_plan": plan,
        "risk_review": review,
    }


async def main():
    symbol = "0939.HK"
    result = await run_symbol(symbol)
    pprint(result)


if __name__ == "__main__":
    asyncio.run(main())


