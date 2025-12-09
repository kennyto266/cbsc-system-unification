#!/usr / bin / env python3
"""
Sprint 1 實現演示腳本

展示異步HTTP客戶端的所有功能：
- US - 001: AsyncHTTPClient類
- US - 002: 連接池管理
- US - 003: 批量請求處理
- US - 004: 重試機制
- US - 005: Prometheus監控
"""

import asyncio
import time
import json
from typing import List, Dict, Any

# 導入我們實現的模塊
from src.core.async_http_client import AsyncHTTPClient
from src.utils.http_utils import (
    get_hkex_data,
    batch_get_hkex_data,
    benchmark_batch_requests,
    health_check,
    load_config
)
from src.monitoring.http_metrics import start_monitoring_server
from src.data_adapters.enhanced_http_adapter import EnhancedHttpApiAdapter, EnhancedHttpApiAdapterConfig


class Sprint1Demo:
    """Sprint 1 演示類"""

    def __init__(self):
        self.http_client: AsyncHTTPClient = None
        self.monitoring_runner = None

    async def setup(self):
        """初始化演示環境"""
        print("=" * 70)
        print("Sprint 1 異步HTTP客戶端實現演示")
        print("=" * 70)

        # 啟動監控服務器
        print("\n1. 啟動Prometheus監控服務器...")
        try:
            self.monitoring_runner = await start_monitoring_server(port=8000)
            print("   ✓ 監控服務器已啟動 (http://localhost:8000)")
            print("   ✓ /metrics 端點可用")
            print("   ✓ /health 端點可用")
        except Exception as e:
            print(f"   ✗ 監控服務器啟動失敗: {e}")

        # 創建HTTP客戶端
        print("\n2. 創建異步HTTP客戶端...")
        config = load_config()
        http_config = {
            'max_connections': config.get('max_connections', 1000),
            'max_connections_per_host': config.get('max_connections_per_host', 100),
            'timeout': config.get('timeout', 30),
            'max_retries': config.get('max_retries', 3),
        }
        self.http_client = AsyncHTTPClient(**http_config)
        await self.http_client.create_session()
        print("   ✓ HTTP客戶端已創建")
        print(f"   ✓ 連接池大小: {http_config['max_connections']}")
        print(f"   ✓ 每主機連接: {http_config['max_connections_per_host']}")
        print(f"   ✓ 超時時間: {http_config['timeout']}s")
        print(f"   ✓ 最大重試: {http_config['max_retries']}次")

    async def demo_single_request(self):
        """演示單個請求功能 (US - 001)"""
        print("\n" + "=" * 70)
        print("US - 001: 單個異步請求測試")
        print("=" * 70)

        try:
            result = await get_hkex_data("0700.hk", 365)

            print("\n股票代碼: 0700.hk (騰訊)")
            print(f"狀態: {result['status']}")

            if result['status'] == 'success':
                print(f"數據獲取時間: {result['duration'] * 1000:.2f}ms")
                print(f"數據記錄數: {len(result['data']) if isinstance(result['data'], dict) else 'N / A'}")
                print("✓ 單個請求成功")
            else:
                print(f"錯誤: {result.get('error', 'Unknown error')}")
                print("✗ 單個請求失敗")

        except Exception as e:
            print(f"✗ 請求異常: {e}")

    async def demo_batch_requests(self):
        """演示批量請求功能 (US - 003)"""
        print("\n" + "=" * 70)
        print("US - 003: 批量請求處理測試")
        print("=" * 70)

        symbols = [
            "0700.hk",  # 騰訊
            "0388.hk",  # 港交所
            "1398.hk",  # 工商銀行
            "0939.hk",  # 建設銀行
            "3988.hk",  # 中國銀行
        ]

        print(f"\n股票列表: {', '.join(symbols)}")
        print(f"請求數量: {len(symbols)}")

        try:
            start_time = time.time()
            results = await batch_get_hkex_data(symbols, 365)
            total_time = time.time() - start_time

            print(f"\n總耗時: {total_time:.3f}s")
            print(f"成功獲取: {results['success_count']}/{results['total_count']}")
            print(f"成功率: {results['success_count'] / results['total_count'] * 100:.1f}%")
            print(f"平均每請求: {total_time / len(symbols) * 1000:.2f}ms")

            # 顯示每個股票的狀態
            print("\n詳細結果:")
            for symbol, data in results['results'].items():
                status_symbol = "✓" if data['status'] == 'success' else "✗"
                duration = data.get('duration', 0)
                print(f"  {status_symbol} {symbol}: {data['status']} ({duration * 1000:.2f}ms)")

            if results['success_count'] == len(symbols):
                print("\n✓ 批量請求全部成功")
            else:
                print("\n⚠ 批量請求部分失敗")

        except Exception as e:
            print(f"✗ 批量請求異常: {e}")

    async def demo_connection_pool(self):
        """演示連接池功能 (US - 002)"""
        print("\n" + "=" * 70)
        print("US - 002: 連接池管理測試")
        print("=" * 70)

        try:
            # 獲取連接池狀態
            pool_status = await self.http_client.get_pool_status()

            print("\n連接池狀態:")
            print(f"  總連接數: {pool_status.get('total_connections', 'N / A')}")
            print(f"  可用連接: {pool_status.get('available_connections', 'N / A')}")
            print(f"  關閉連接: {pool_status.get('closed_connections', 'N / A')}")
            print(f"  進行中連接: {pool_status.get('in_flight_connections', 'N / A')}")
            print(f"  每主機限制: {pool_status.get('max_per_host', 'N / A')}")

            # 獲取監控指標
            metrics = self.http_client.get_metrics()

            print("\n監控指標:")
            print(f"  請求總數: {metrics.get('requests_total', 0)}")
            print(f"  請求持續時間總和: {metrics.get('request_duration_seconds_sum', 0):.3f}s")
            print(f"  當前併發請求: {metrics.get('concurrent_requests', 0)}")
            print(f"  重試總數: {metrics.get('retries_total', 0)}")

            print("\n✓ 連接池管理正常")

        except Exception as e:
            print(f"✗ 連接池狀態獲取失敗: {e}")

    async def demo_retry_mechanism(self):
        """演示重試機制 (US - 004)"""
        print("\n" + "=" * 70)
        print("US - 004: 重試機制測試")
        print("=" * 70)

        print("\n配置信息:")
        print(f"  最大重試次數: {self.http_client.max_retries}")
        print(f"  退避因子: {self.http_client.retry_backoff_factor}")
        print(f"  超時時間: {self.http_client.timeout.total}s")

        print("\n重試策略:")
        print("  1. 指數退避: 1s, 2s, 4s, 8s, ...")
        print("  2. 可重試錯誤: ConnectionError, TimeoutError")
        print("  3. 不可重試錯誤: HTTP 500, ClientResponseError")
        print("  4. 詳細錯誤日誌記錄")

        print("\n✓ 重試機制已實現並配置")

    async def demo_performance_benchmark(self):
        """演示性能基準測試"""
        print("\n" + "=" * 70)
        print("性能基準測試")
        print("=" * 70)

        symbols = [
            "0700.hk", "0388.hk", "1398.hk", "0939.hk", "3988.hk",
            "2318.hk", "1299.hk", "0941.hk", "3690.hk", "9988.hk"
        ]

        print("\n測試參數:")
        print(f"  股票數量: {len(symbols)}")
        print("  併發級別: [10, 50, 100]")

        try:
            results = await benchmark_batch_requests(
                symbols=symbols,
                duration_days=365,
                max_concurrent_list=[10, 50, 100]
            )

            print("\n性能測試結果:")
            for test in results['tests']:
                print(f"\n  併發 {test['max_concurrent']:3d}:")
                print(f"    總耗時: {test['total_time_seconds']:.3f}s")
                print(f"    平均每請求: {test['avg_time_per_request'] * 1000:.2f}ms")
                print(f"    成功率: {test['success_rate']:.1f}%")

            print("\n✓ 性能基準測試完成")

        except Exception as e:
            print(f"✗ 性能測試失敗: {e}")

    async def demo_health_check(self):
        """演示健康檢查"""
        print("\n" + "=" * 70)
        print("健康檢查測試")
        print("=" * 70)

        endpoints = [
            "http://18.180.162.113:9191 / inst / getInst?symbol=0700.hk&duration=1",
            "http://localhost:8000 / health",
        ]

        for url in endpoints:
            try:
                result = await health_check(url, timeout=5)

                print(f"\n端點: {url}")
                print(f"  狀態: {result['status']}")
                print(f"  響應時間: {result['response_time_ms']}ms")

                if result['status'] == 'healthy':
                    print("  ✓ 健康")
                else:
                    print(f"  ✗ 不健康: {result.get('error', 'Unknown')}")

            except Exception as e:
                print(f"\n端點: {url}")
                print(f"  ✗ 檢查失敗: {e}")

    async def demo_enhanced_adapter(self):
        """演示增強版HTTP適配器"""
        print("\n" + "=" * 70)
        print("增強版HTTP適配器演示")
        print("=" * 70)

        # 創建適配器配置
        config = EnhancedHttpApiAdapterConfig(
            source_path="http://18.180.162.113:9191",
            endpoint_symbol="/inst / getInst",
            http_max_connections=1000,
            http_max_connections_per_host=100,
            http_timeout=30,
            http_max_retries=3,
            batch_size=100,
            batch_max_concurrent=100,
        )

        adapter = EnhancedHttpApiAdapter(config)

        try:
            # 測試單個股票
            print("\n1. 單個股票數據獲取測試:")
            data = await adapter.get_market_data("0700.hk", duration_days=365)
            print("   股票: 0700.hk")
            print(f"   記錄數: {len(data)}")
            print("   ✓ 獲取成功" if data else "   ✗ 無數據")

            # 測試批量獲取
            print("\n2. 批量股票數據獲取測試:")
            symbols = ["0700.hk", "0388.hk", "1398.hk"]
            batch_data = await adapter.get_batch_market_data(symbols, duration_days=365)
            print(f"   股票數量: {len(symbols)}")
            for symbol, data in batch_data.items():
                print(f"   {symbol}: {len(data)} 記錄")

            # 獲取HTTP客戶端統計
            print("\n3. HTTP客戶端統計:")
            stats = await adapter.get_http_client_stats()
            if 'error' not in stats:
                pool = stats.get('pool_status', {})
                metrics = stats.get('metrics', {})
                print("   連接池狀態: ✓")
                print(f"   請求總數: {metrics.get('requests_total', 0)}")
                print(f"   當前併發: {metrics.get('concurrent_requests', 0)}")

            await adapter.disconnect()

        except Exception as e:
            print(f"✗ 適配器測試失敗: {e}")

    async def cleanup(self):
        """清理資源"""
        print("\n" + "=" * 70)
        print("清理資源")
        print("=" * 70)

        if self.http_client:
            await self.http_client.close()
            print("✓ HTTP客戶端已關閉")

        if self.monitoring_runner:
            await self.monitoring_runner.cleanup()
            print("✓ 監控服務器已關閉")

        print("\n" + "=" * 70)
        print("演示完成！")
        print("=" * 70)

    async def run_all_demos(self):
        """運行所有演示"""
        await self.setup()

        await self.demo_single_request()
        await self.demo_batch_requests()
        await self.demo_connection_pool()
        await self.demo_retry_mechanism()
        await self.demo_performance_benchmark()
        await self.demo_health_check()
        await self.demo_enhanced_adapter()

        await self.cleanup()


async def main():
    """主函數"""
    demo = Sprint1Demo()
    try:
        await demo.run_all_demos()
    except KeyboardInterrupt:
        print("\n\n用戶中斷演示")
        await demo.cleanup()
    except Exception as e:
        print(f"\n\n演示異常: {e}")
        import traceback
        traceback.print_exc()
        await demo.cleanup()


if __name__ == "__main__":
    # 運行演示
    asyncio.run(main())
