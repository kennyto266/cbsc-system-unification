import asyncio
from pprint import pprint
from typing import List

from src.data_adapters.data_service import DataService
from src.agents.real_agents.base_real_agent import RealAgentConfig
from src.core.message_queue import Message
from scripts.agent_http_pipeline import QAAgentConcrete


async def run_for_symbol(ds: DataService, symbol: str) -> None:
    data = await ds.get_market_data(symbol, source_preference="http_api")
    print(f"\n=== {symbol} ===")
    print(f"market_data records: {len(data)}")
    if not data:
        return

    cfg = RealAgentConfig(
        agent_id=f"qa_http_{symbol.replace('.','_').lower()}",
        agent_type="quantitative_analyst",
        name=f"QA_{symbol}",
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
    ok = await agent.initialize()
    print("agent init:", ok)
    if not ok:
        return

    analysis = await agent.analyze_market_data(data)
    pprint({
        "symbols": analysis.symbols_analyzed,
        "signal_strength": analysis.signal_strength,
        "direction": analysis.signal_direction,
        "confidence": analysis.confidence,
    })

    signals = await agent.generate_trading_signals(analysis)
    print(f"signals: {len(signals)}")
    if signals:
        pprint(signals[:3])
        exec_res = await agent.execute_strategy(signals)
        print("execution:")
        pprint(exec_res)

    await agent.cleanup()


async def main(symbols: List[str]) -> None:
    ds = DataService()
    ok = await ds.initialize()
    if not ok:
        print("DataService 初始化失败")
        return

    # 顺序执行以配合 http_api 限频，也可改为受限并发
    for s in symbols:
        await run_for_symbol(ds, s)

    await ds.cleanup()


if __name__ == "__main__":
    # 可按需调整符号列表
    symbols = ["0939.HK", "2800.HK"]
    asyncio.run(main(symbols))


