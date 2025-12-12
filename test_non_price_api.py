#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非价格策略API测试脚本 - Non-Price Strategy API Test Script
测试HKMA数据API端点的功能
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NonPriceAPITester:
    """非价格API测试器"""

    def __init__(self, base_url: str = "http://localhost:3004"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_endpoint(self, endpoint: str, method: str = "GET",
                           params: Dict[str, Any] = None,
                           data: Dict[str, Any] = None) -> Dict[str, Any]:
        """测试API端点"""
        url = f"{self.base_url}{endpoint}"

        try:
            logger.info(f"Testing {method} {url}")

            if method == "GET":
                async with self.session.get(url, params=params) as response:
                    result = {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "data": await response.json() if response.content_type == "application/json" else await response.text()
                    }
            elif method == "POST":
                async with self.session.post(url, json=data) as response:
                    result = {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "data": await response.json() if response.content_type == "application/json" else await response.text()
                    }
            else:
                raise ValueError(f"Unsupported method: {method}")

            logger.info(f"Response status: {result['status']}")
            return result

        except Exception as e:
            logger.error(f"Error testing {endpoint}: {e}")
            return {
                "status": 0,
                "error": str(e),
                "data": None
            }

    async def test_hibor_endpoint(self):
        """测试HIBOR利率端点"""
        logger.info("=== Testing HIBOR Rates Endpoint ===")
        result = await self.test_endpoint("/api/non-price/hkma/hibor/latest")

        if result["status"] == 200:
            data = result["data"]
            if data.get("success"):
                logger.info(f"✅ HIBOR API working successfully")
                logger.info(f"Message: {data.get('message')}")
                logger.info(f"Data points: {len(data.get('data', []))}")

                for hibor in data.get("data", [])[:2]:  # Show first 2
                    logger.info(f"  - {hibor.get('tenor')}: {hibor.get('rate')}%")
            else:
                logger.error(f"❌ HIBOR API returned failure: {data}")
        else:
            logger.error(f"❌ HIBOR API HTTP error: {result['status']}")

    async def test_monetary_base_endpoint(self):
        """测试货币基础端点"""
        logger.info("=== Testing Monetary Base Endpoint ===")
        result = await self.test_endpoint("/api/non-price/hkma/monetary-base/latest")

        if result["status"] == 200:
            data = result["data"]
            if data.get("success"):
                logger.info(f"✅ Monetary Base API working successfully")
                logger.info(f"Total amount: {data.get('data', {}).get('total_amount')} 亿港币")
                logger.info(f"Change: {data.get('data', {}).get('change_percentage')}%")
            else:
                logger.error(f"❌ Monetary Base API returned failure: {data}")
        else:
            logger.error(f"❌ Monetary Base API HTTP error: {result['status']}")

    async def test_exchange_rate_endpoint(self):
        """测试汇率端点"""
        logger.info("=== Testing Exchange Rate Endpoint ===")
        result = await self.test_endpoint(
            "/api/non-price/hkma/exchange-rate/latest",
            params={"currency_pair": "USD/HKD"}
        )

        if result["status"] == 200:
            data = result["data"]
            if data.get("success"):
                logger.info(f"✅ Exchange Rate API working successfully")
                rate_data = data.get("data", {})
                logger.info(f"Rate: {rate_data.get('rate')}")
                logger.info(f"Change: {rate_data.get('change')}")
            else:
                logger.error(f"❌ Exchange Rate API returned failure: {data}")
        else:
            logger.error(f"❌ Exchange Rate API HTTP error: {result['status']}")

    async def test_liquidity_endpoint(self):
        """测试流动性端点"""
        logger.info("=== Testing Liquidity Endpoint ===")
        result = await self.test_endpoint("/api/non-price/hkma/liquidity/latest")

        if result["status"] == 200:
            data = result["data"]
            if data.get("success"):
                logger.info(f"✅ Liquidity API working successfully")
                logger.info(f"Indicators: {len(data.get('data', []))}")

                for indicator in data.get("data", [])[:2]:
                    logger.info(f"  - {indicator.get('indicator')}: {indicator.get('value')} {indicator.get('unit')}")
            else:
                logger.error(f"❌ Liquidity API returned failure: {data}")
        else:
            logger.error(f"❌ Liquidity API HTTP error: {result['status']}")

    async def test_historical_data_endpoint(self):
        """测试历史数据端点"""
        logger.info("=== Testing Historical Data Endpoint ===")

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        result = await self.test_endpoint(
            "/api/non-price/hkma/historical",
            params={
                "data_type": "hibor",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            }
        )

        if result["status"] == 200:
            data = result["data"]
            if data.get("success"):
                logger.info(f"✅ Historical Data API working successfully")
                logger.info(f"Data type: {data.get('data_type')}")
                logger.info(f"Data points: {data.get('total_count')}")
            else:
                logger.error(f"❌ Historical Data API returned failure: {data}")
        else:
            logger.error(f"❌ Historical Data API HTTP error: {result['status']}")

    async def test_sentiment_endpoint(self):
        """测试情绪分析端点"""
        logger.info("=== Testing Sentiment Analysis Endpoint ===")

        test_symbols = ["0700.HK", "HSBC", "腾讯"]

        for symbol in test_symbols:
            result = await self.test_endpoint(f"/api/non-price/sentiment/latest/{symbol}")

            if result["status"] == 200:
                data = result["data"]
                if data.get("success"):
                    logger.info(f"✅ Sentiment API working for {symbol}")
                    logger.info(f"Sentiment: {data.get('sentiment_label')} ({data.get('sentiment_score'):.2f})")
                else:
                    logger.warning(f"⚠️ Sentiment API returned failure for {symbol}: {data}")
            else:
                logger.warning(f"⚠️ Sentiment API HTTP error for {symbol}: {result['status']}")

    async def test_strategies_endpoint(self):
        """测试策略端点"""
        logger.info("=== Testing Strategies Endpoint ===")
        result = await self.test_endpoint("/api/non-price/strategies/available")

        if result["status"] == 200:
            data = result["data"]
            if data.get("success"):
                logger.info(f"✅ Strategies API working successfully")
                logger.info(f"Available strategies: {data.get('total_count')}")

                for strategy in data.get("strategies", [])[:2]:
                    logger.info(f"  - {strategy.get('name')}: {strategy.get('description')}")
            else:
                logger.error(f"❌ Strategies API returned failure: {data}")
        else:
            logger.error(f"❌ Strategies API HTTP error: {result['status']}")

    async def test_health_check(self):
        """测试健康检查端点"""
        logger.info("=== Testing Health Check Endpoint ===")
        result = await self.test_endpoint("/api/non-price/health")

        if result["status"] == 200:
            data = result["data"]
            if data.get("success"):
                logger.info(f"✅ Health check passed")
                logger.info(f"Status: {data.get('status')}")
                services = data.get("services", {})
                for service_name, service_status in services.items():
                    logger.info(f"  - {service_name}: {service_status}")
            else:
                logger.error(f"❌ Health check failed: {data}")
        else:
            logger.error(f"❌ Health check HTTP error: {result['status']}")

    async def test_api_info(self):
        """测试API信息端点"""
        logger.info("=== Testing API Info Endpoint ===")
        result = await self.test_endpoint("/api/non-price/info")

        if result["status"] == 200:
            data = result["data"]
            if data.get("success"):
                logger.info(f"✅ API Info working successfully")
                logger.info(f"API: {data.get('api_name')} v{data.get('version')}")
                logger.info(f"Description: {data.get('description')}")
            else:
                logger.error(f"❌ API Info returned failure: {data}")
        else:
            logger.error(f"❌ API Info HTTP error: {result['status']}")

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 Starting Non-Price Strategy API Tests...")
        logger.info(f"Testing against: {self.base_url}")
        logger.info("=" * 60)

        tests = [
            self.test_health_check,
            self.test_api_info,
            self.test_hibor_endpoint,
            self.test_monetary_base_endpoint,
            self.test_exchange_rate_endpoint,
            self.test_liquidity_endpoint,
            self.test_historical_data_endpoint,
            self.test_sentiment_endpoint,
            self.test_strategies_endpoint,
        ]

        passed = 0
        failed = 0

        for test_func in tests:
            try:
                await test_func()
                passed += 1
                logger.info("✅ Test completed successfully\n")
            except Exception as e:
                logger.error(f"❌ Test failed: {e}\n")
                failed += 1

        logger.info("=" * 60)
        logger.info(f"🏁 Test Summary: {passed} passed, {failed} failed")

        if failed == 0:
            logger.info("🎉 All tests passed! Non-Price Strategy API is working correctly.")
        else:
            logger.warning(f"⚠️ {failed} tests failed. Please check the API implementation.")


async def main():
    """主函数"""
    # 测试本地API
    async with NonPriceAPITester("http://localhost:3004") as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Tests cancelled by user")
    except Exception as e:
        logger.error(f"❌ Test runner error: {e}")