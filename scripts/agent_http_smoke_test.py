import asyncio
from pprint import pprint

from src.data_adapters.data_service import DataService
from src.agents.real_agents.real_data_analyzer import RealDataAnalyzer
from src.agents.real_agents.base_real_agent import RealAgentConfig


async def main():
    # 1) 准备数据服务（http_api）
    ds = DataService()
    ok = await ds.initialize()
    if not ok:
        print("DataService 初始化失败")
        return

    symbol = "0939.HK"
    data = await ds.get_market_data(symbol, source_preference="http_api")
    print(f"market_data records: {len(data)}")
    if not data:
        await ds.cleanup()
        return

    # 2) 使用 RealDataAnalyzer 执行分析（避免抽象类实例化问题）
    cfg = RealAgentConfig(
        agent_id="qa_http_smoke",
        agent_type="quantitative_analyst",
        name="QA_HTTP_SMOKE",
        data_sources=["http_api"],
        update_frequency=60,
        lookback_period=60,
        analysis_methods=["technical", "regime"],
        signal_threshold=0.2,
        confidence_threshold=0.2,
        ml_models=[],
        performance_tracking=False,
        backtest_enabled=False,
    )
    analyzer = RealDataAnalyzer(cfg)
    await analyzer.initialize()

    analysis = await analyzer.analyze(data)
    print("analysis summary:")
    pprint({
        "symbols": analysis.symbols_analyzed,
        "signal_strength": analysis.signal_strength,
        "direction": analysis.signal_direction,
        "confidence": analysis.confidence,
        "regime": analysis.market_regime.model_dump() if analysis.market_regime else None,
        "insights": analysis.insights[:3],
        "warnings": analysis.warnings[:3],
    })

    # 3) 清理
    await analyzer.cleanup()
    await ds.cleanup()


if __name__ == "__main__":
    asyncio.run(main())


