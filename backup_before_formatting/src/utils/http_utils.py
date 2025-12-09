"""
HTTP客戶端實用工具函數

為港股量化交易系統提供便捷的HTTP請求封裝
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# 導入AsyncHTTPClient
try:
    from src.core.async_http_client import AsyncHTTPClient
except ImportError:
    # 如果路徑不存在，使用相對導入
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.async_http_client import AsyncHTTPClient

# 默認配置文件路徑
DEFAULT_CONFIG_PATH = (
    Path(__file__).parent.parent.parent / "config" / "http_client.yaml"
)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加載HTTP客戶端配置

    Args:
        config_path: 配置文件路徑，如果為None則使用默認路徑

    Returns:
        配置字典
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    try:
        with open(path, "r", encoding="utf - 8") as f:
            config = yaml.safe_load(f)
            return config.get("http_client", {})
    except FileNotFoundError:
        print(f"Warning: Config file {path} not found, using default values")
        return {}
    except Exception as e:
        print(f"Warning: Failed to load config: {e}")
        return {}


async def get_hkex_data(symbol: str, duration_days: int = 365) -> Dict[str, Any]:
    """
    獲取港交所股票數據

    Args:
        symbol: 股票代碼 (小寫，如 '0700.hk')
        duration_days: 持續時間（天）

    Returns:
        股票數據字典
    """
    config = load_config()
    http_config = {
        "max_connections": config.get("max_connections", 1000),
        "max_connections_per_host": config.get("max_connections_per_host", 100),
        "timeout": config.get("timeout", 30),
        "max_retries": config.get("max_retries", 3),
        "retry_backoff_factor": config.get("retry_backoff_factor", 2.0),
    }

    async with AsyncHTTPClient(**http_config) as client:
        url = "http://18.180.162.113:9191 / inst / getInst"
        params = {"symbol": symbol.lower(), "duration": duration_days}

        result = await client.get(url, params=params)

        if result.get("success"):
            return {
                "symbol": symbol,
                "data": result["data"],
                "duration": result["duration"],
                "status": "success",
            }
        else:
            return {
                "symbol": symbol,
                "error": result.get("error", "Unknown error"),
                "status": "failed",
            }


async def batch_get_hkex_data(
    symbols: List[str], duration_days: int = 365
) -> Dict[str, Any]:
    """
    批量獲取港交所股票數據

    Args:
        symbols: 股票代碼列表
        duration_days: 持續時間（天）

    Returns:
        所有股票數據字典
    """
    config = load_config()
    http_config = {
        "max_connections": config.get("max_connections", 1000),
        "max_connections_per_host": config.get("max_connections_per_host", 100),
        "timeout": config.get("timeout", 30),
        "max_retries": config.get("max_retries", 3),
        "retry_backoff_factor": config.get("retry_backoff_factor", 2.0),
    }

    batch_config = config.get("batch", {})
    max_concurrent = batch_config.get("max_concurrent", 100)

    async with AsyncHTTPClient(**http_config) as client:
        requests = [
            {
                "method": "GET",
                "url": "http://18.180.162.113:9191 / inst / getInst",
                "params": {"symbol": symbol.lower(), "duration": duration_days},
            }
            for symbol in symbols
        ]

        results = await client.batch_request(requests, max_concurrent=max_concurrent)

        # 整理結果
        data = {}
        for i, result in enumerate(results):
            symbol = symbols[i]
            if result.get("success"):
                data[symbol] = {
                    "data": result["data"],
                    "duration": result["duration"],
                    "status": "success",
                }
            else:
                data[symbol] = {
                    "error": result.get("error", "Unknown error"),
                    "status": "failed",
                }

        return {
            "symbols": symbols,
            "results": data,
            "success_count": sum(1 for r in results if r.get("success")),
            "total_count": len(symbols),
        }


async def get_multiple_symbols(
    symbols: List[str], duration_days: int = 365, max_concurrent: int = 50
) -> Dict[str, Any]:
    """
    獲取多個股票數據（別名函數）

    Args:
        symbols: 股票代碼列表
        duration_days: 持續時間（天）
        max_concurrent: 最大併發數

    Returns:
        股票數據字典
    """
    config = load_config()
    http_config = {
        "max_connections": config.get("max_connections", 1000),
        "max_connections_per_host": config.get("max_connections_per_host", 100),
        "timeout": config.get("timeout", 30),
        "max_retries": config.get("max_retries", 3),
        "retry_backoff_factor": config.get("retry_backoff_factor", 2.0),
    }

    async with AsyncHTTPClient(**http_config) as client:
        requests = [
            {
                "method": "GET",
                "url": "http://18.180.162.113:9191 / inst / getInst",
                "params": {"symbol": symbol.lower(), "duration": duration_days},
            }
            for symbol in symbols
        ]

        results = await client.batch_request(requests, max_concurrent=max_concurrent)

        # 整理結果
        data = {}
        for i, result in enumerate(results):
            symbol = symbols[i]
            if result.get("success"):
                data[symbol] = result["data"]
            else:
                data[symbol] = {"error": result.get("error", "Unknown error")}

        return data


async def health_check(url: str, timeout: int = 5) -> Dict[str, Any]:
    """
    檢查HTTP端點健康狀態

    Args:
        url: 要檢查的URL
        timeout: 超時時間（秒）

    Returns:
        健康檢查結果
    """
    config = load_config()
    http_config = {
        "max_connections": 10,
        "max_connections_per_host": 10,
        "timeout": timeout,
        "max_retries": 1,
    }

    start_time = asyncio.get_event_loop().time()

    try:
        async with AsyncHTTPClient(**http_config) as client:
            result = await client.get(url)

            duration = asyncio.get_event_loop().time() - start_time

            return {
                "url": url,
                "status": "healthy" if result.get("success") else "unhealthy",
                "response_time_ms": round(duration * 1000, 2),
                "status_code": result.get("status"),
                "error": result.get("error") if not result.get("success") else None,
            }

    except Exception as e:
        duration = asyncio.get_event_loop().time() - start_time
        return {
            "url": url,
            "status": "unhealthy",
            "response_time_ms": round(duration * 1000, 2),
            "error": str(e),
        }


async def benchmark_batch_requests(
    symbols: List[str],
    duration_days: int = 365,
    max_concurrent_list: List[int] = [10, 50, 100],
) -> Dict[str, Any]:
    """
    批量請求性能基準測試

    Args:
        symbols: 股票代碼列表
        duration_days: 持續時間（天）
        max_concurrent_list: 要測試的併發數列表

    Returns:
        基準測試結果
    """
    results = {"symbols_count": len(symbols), "tests": []}

    for max_concurrent in max_concurrent_list:
        print(f"\n測試併發數: {max_concurrent}")

        start_time = asyncio.get_event_loop().time()

        data = await get_multiple_symbols(
            symbols=symbols, duration_days=duration_days, max_concurrent=max_concurrent
        )

        total_time = asyncio.get_event_loop().time() - start_time
        success_count = sum(1 for v in data.values() if "error" not in v)

        test_result = {
            "max_concurrent": max_concurrent,
            "total_time_seconds": round(total_time, 3),
            "avg_time_per_request": round(total_time / len(symbols), 3),
            "success_count": success_count,
            "total_count": len(symbols),
            "success_rate": round(success_count / len(symbols) * 100, 2),
        }

        results["tests"].append(test_result)
        print(f"  總耗時: {test_result['total_time_seconds']}s")
        print(f"  平均每請求: {test_result['avg_time_per_request']}s")
        print(f"  成功率: {test_result['success_rate']}%")

    return results


if __name__ == "__main__":
    # 測試代碼
    async def test():
        # 測試單個請求
        print("測試單個請求...")
        result = await get_hkex_data("0700.hk", 365)
        print(f"結果: {result['status']}")

        # 測試批量請求
        print("\n測試批量請求...")
        symbols = ["0700.hk", "0388.hk", "1398.hk"]
        results = await batch_get_hkex_data(symbols, 365)
        print(f"成功獲取: {results['success_count']}/{results['total_count']}")

    # 運行測試（僅在直接執行文件時）
    asyncio.run(test())
