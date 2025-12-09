import asyncio
from pprint import pprint
from typing import Any, Dict, List, Optional

from src.data_adapters.data_service import DataService
from src.agents.real_agents.real_quantitative_analyst import RealQuantitativeAnalyst
from src.agents.real_agents.base_real_agent import RealAgentConfig
from src.core.message_queue import Message


class QAAgentConcrete(RealQuantitativeAnalyst):
    """具体可运行版量化分析师Agent：
    - 实现必要抽象方法
    - 将 process_message 委托给 handle_message
    """

    async def _initialize_specific(self) -> bool:
        return True

    async def _enhance_analysis(self, base_result, market_data):
        # 简单直传，可在此叠加自定义逻辑
        return base_result

    async def _enhance_signals(self, base_signals, analysis_result):
        # 简单直传，可在此二次加工
        return base_signals

    async def _execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        # 演示：不实际下单，仅返回执行回执
        return {"symbol": signal.get("symbol"), "executed": True, "detail": signal}

    async def process_message(self, message: Message) -> bool:
        # 委托给基类的 handle_message
        _ = await self.handle_message(message)
        return True


async def main():
    symbol = "0939.HK"

    # 1) 数据服务（http_api）
    ds = DataService()
    ok = await ds.initialize()
    if not ok:
        print("DataService 初始化失败")
        return

    data = await ds.get_market_data(symbol, source_preference="http_api")
    print(f"market_data records: {len(data)}")
    if not data:
        await ds.cleanup()
        return

    # 2) Agent 实例化与初始化
    cfg = RealAgentConfig(
        agent_id="qa_http_pipeline",
        agent_type="quantitative_analyst",
        name="QA_HTTP_PIPELINE",
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
        await ds.cleanup()
        return

    # 3) 分析 → 信号生成
    analysis = await agent.analyze_market_data(data)
    print("analysis summary:")
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

    # 4) 清理
    await agent.cleanup()
    await ds.cleanup()


if __name__ == "__main__":
    asyncio.run(main())


