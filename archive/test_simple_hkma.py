#!/usr/bin/env python3
"""
簡化測試HKMA數據集成
"""

import asyncio
from hkma_data_integration import get_hkma_data_for_optimizer

def test_simple_hkma():
    """簡化測試"""
    print("🧪 簡化HKMA數據測試")

    test_data_sources = {
        'HB': 'HIBOR利率數據',
        'MB': '貨幣基礎數據'
    }

    async def get_data():
        return await get_hkma_data_for_optimizer(test_data_sources, 10)

    try:
        # 運行異步任務
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            data = loop.run_until_complete(get_data())
            print(f"✅ 成功獲取數據: {data}")
            return True
        finally:
            loop.close()
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    test_simple_hkma()