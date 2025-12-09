import asyncio
from pprint import pprint

from src.data_adapters.data_service import DataService


async def main():
    ds = DataService()
    ok = await ds.initialize()
    if not ok:
        print("DataService 初始化失败")
        return

    data = await ds.get_market_data("0939.HK", source_preference="http_api")
    print("records:", len(data))
    if data:
        pprint(data[0].model_dump())

    await ds.cleanup()


if __name__ == "__main__":
    asyncio.run(main())


