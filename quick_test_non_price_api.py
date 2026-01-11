#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证非价格策略API - Quick Non-Price API Validation
简单测试HKMA API端点是否正常工作
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_non_price_service():
    """测试非价格服务"""
    try:
        print("🔧 Testing Non-Price Service...")

        # 导入服务
        from src.api.services.non_price_service import get_non_price_service
        service = get_non_price_service()

        # 测试HIBOR数据
        print("  📈 Testing HIBOR data...")
        hibor_rates = await service.get_latest_hibor_rates()
        print(f"    ✅ Got {len(hibor_rates)} HIBOR rates")
        for rate in hibor_rates[:2]:
            print(f"      - {rate.tenor}: {rate.rate}%")

        # 测试货币基础数据
        print("  💰 Testing Monetary Base data...")
        monetary_base = await service.get_latest_monetary_base()
        print(f"    ✅ Monetary Base: {monetary_base.total_amount} 亿港币")

        # 测试汇率数据
        print("  💱 Testing Exchange Rate data...")
        exchange_rate = await service.get_latest_exchange_rate()
        print(f"    ✅ USD/HKD Rate: {exchange_rate.rate}")

        # 测试流动性数据
        print("  💧 Testing Liquidity data...")
        liquidity_data = await service.get_latest_liquidity_data()
        print(f"    ✅ Got {len(liquidity_data)} liquidity indicators")

        # 测试情绪分析
        print("  💭 Testing Sentiment Analysis...")
        sentiment_signals = await service.get_sentiment_signals("0700.HK")
        print(f"    ✅ Got {len(sentiment_signals)} sentiment signals")

        # 测试策略列表
        print("  🎯 Testing Strategy List...")
        strategies = await service.get_available_strategies()
        print(f"    ✅ Got {len(strategies)} available strategies")

        print("🎉 All service tests passed!")
        return True

    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False

async def test_api_models():
    """测试API模型"""
    try:
        print("🔧 Testing API Models...")

        from src.api.models.non_price_responses import (
            HIBORRate,
            MonetaryBaseData,
            ExchangeRateData,
            NonPriceSignal,
            APIConfiguration
        )

        # 创建测试模型实例
        hibor = HIBORRate(
            tenor="1M",
            rate=5.75,
            change=0.05,
            timestamp=datetime.utcnow()
        )
        print(f"  ✅ HIBORRate model: {hibor.tenor} = {hibor.rate}%")

        monetary_base = MonetaryBaseData(
            total_amount=18500.5,
            change_amount=125.3,
            change_percentage=0.68,
            timestamp=datetime.utcnow()
        )
        print(f"  ✅ MonetaryBaseData model: {monetary_base.total_amount} 亿港币")

        signal = NonPriceSignal(
            signal_id="test_signal",
            signal_type="hibor",
            source="hkma",
            value=5.75,
            confidence=0.95,
            timestamp=datetime.utcnow()
        )
        print(f"  ✅ NonPriceSignal model: {signal.signal_id}")

        print("🎉 All model tests passed!")
        return True

    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 Starting Quick Non-Price API Validation...")
    print("=" * 50)

    # 测试模型
    model_ok = await test_api_models()
    print()

    # 测试服务
    service_ok = await test_non_price_service()
    print()

    print("=" * 50)
    if model_ok and service_ok:
        print("🎉 SUCCESS: Non-Price API implementation is working correctly!")
        print("✅ Ready to start the API server and test endpoints")
        return 0
    else:
        print("❌ FAILURE: Some components are not working properly")
        print("🔧 Please check the errors above and fix the issues")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)